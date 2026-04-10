from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import ComplianceFramework, Clause, Control, Document, Guideline
from .forms import DocumentForm


# ---------------------------------------------------------------------------
# Framework / control seeding
# ---------------------------------------------------------------------------

# Maps industry -> list of (framework_name, framework_description, clauses_and_controls)
# Each clause_and_controls entry: (clause_number, clause_title, clause_desc, [(ctrl_title, ctrl_desc, mandatory)])

FRAMEWORK_DATA = {
    # ----- ISO 27001 (applicable to it_saas, banking, insurance, government) -----
    'ISO 27001': {
        'description': 'Information Security Management System (ISMS) standard',
        'industries': ['it_saas', 'banking', 'insurance', 'government'],
        'clauses': [
            ('A.5', 'Information Security Policies', 'Policies for information security', [
                ('Information Security Policy', 'Establish and maintain an overarching information security policy approved by management.', True),
            ]),
            ('A.6', 'Organisation of Information Security', 'Internal organisation and mobile devices', [
                ('Security Roles and Responsibilities', 'Define and assign all information security responsibilities.', True),
                ('Mobile Device Policy', 'Adopt a policy and supporting measures to manage risks introduced by mobile devices.', False),
            ]),
            ('A.7', 'Human Resource Security', 'Prior to, during, and after employment', [
                ('HR Security - Screening', 'Background verification checks on all candidates for employment shall be carried out.', True),
                ('HR Security - Awareness Training', 'All employees shall receive appropriate security awareness education and training.', True),
            ]),
            ('A.8', 'Asset Management', 'Responsibility for assets and information classification', [
                ('Asset Inventory', 'Maintain an inventory of all assets associated with information and information processing facilities.', True),
                ('Data Classification', 'Classify information in terms of legal requirements, value, criticality, and sensitivity.', True),
            ]),
            ('A.9', 'Access Control', 'Business requirements and user access management', [
                ('Access Control Policy', 'Establish, document, and review an access control policy based on business and security requirements.', True),
                ('User Registration and De-registration', 'Implement a formal user registration and de-registration process for granting access rights.', True),
                ('Privilege Management', 'Restrict and control the allocation and use of privileged access rights.', True),
            ]),
            ('A.10', 'Cryptography', 'Cryptographic controls', [
                ('Cryptography Policy', 'Develop and implement a policy on the use of cryptographic controls for protection of information.', True),
                ('Key Management', 'Develop and implement a policy on the use, protection, and lifetime of cryptographic keys.', True),
            ]),
            ('A.11', 'Physical and Environmental Security', 'Secure areas and equipment', [
                ('Physical Security Perimeter', 'Define security perimeters to protect areas containing sensitive information and processing facilities.', True),
                ('Clean Desk and Clear Screen Policy', 'Adopt a clean desk policy for papers and removable storage media and a clear screen policy.', False),
            ]),
            ('A.12', 'Operations Security', 'Operational procedures and responsibilities', [
                ('Change Management', 'Control changes to the organisation, business processes, information processing facilities, and systems.', True),
                ('Malware Protection', 'Implement detection, prevention, and recovery controls combined with user awareness for malware.', True),
                ('Backup', 'Maintain backup copies of information, software, and system images; test regularly.', True),
            ]),
            ('A.13', 'Communications Security', 'Network security management', [
                ('Network Security', 'Manage and control networks to protect information in systems and applications.', True),
                ('Information Transfer Policies', 'Have formal transfer policies, procedures, and controls to protect information in transit.', True),
            ]),
            ('A.16', 'Information Security Incident Management', 'Incident management and improvements', [
                ('Incident Management Procedure', 'Establish management responsibilities and procedures for prompt and effective incident response.', True),
                ('Incident Reporting', 'Report information security events through appropriate management channels as quickly as possible.', True),
            ]),
            ('A.17', 'Business Continuity Management', 'Information security continuity', [
                ('Business Continuity Planning', 'Determine requirements for information security and continuity in adverse situations.', True),
                ('BCP Testing and Review', 'Verify established and implemented continuity controls at regular intervals.', True),
            ]),
        ],
    },

    # ----- SOC 2 -----
    'SOC 2': {
        'description': 'Service Organization Control 2 - Trust Services Criteria',
        'industries': ['it_saas'],
        'clauses': [
            ('CC1', 'Security - Common Criteria', 'Controls relevant to security across the organization', [
                ('Logical and Physical Access Controls', 'Restrict logical and physical access to information assets to authorised personnel only.', True),
                ('System Operations Monitoring', 'Monitor system operations and detect anomalies that could indicate security incidents.', True),
                ('Change Management Controls', 'Manage changes to infrastructure and software in a controlled manner to prevent unauthorised changes.', True),
            ]),
            ('CC2', 'Availability', 'System availability controls', [
                ('Availability Monitoring', 'Monitor system components and environmental conditions to identify issues affecting availability.', True),
                ('Disaster Recovery Plan', 'Maintain and test a disaster recovery plan to ensure system availability objectives are met.', True),
            ]),
            ('CC3', 'Processing Integrity', 'Completeness, validity, accuracy, timeliness', [
                ('Data Processing Validation', 'Validate that system processing is complete, valid, accurate, and timely.', True),
                ('Error Handling Procedures', 'Identify and address processing errors in a timely manner.', True),
            ]),
            ('CC4', 'Confidentiality', 'Protection of confidential information', [
                ('Confidential Data Identification', 'Identify and classify confidential information and restrict access accordingly.', True),
                ('Confidential Data Disposal', 'Dispose of confidential information in compliance with data retention policies.', True),
            ]),
            ('CC5', 'Privacy', 'Personal information handling', [
                ('Privacy Notice and Consent', 'Provide notice and obtain consent regarding the collection and use of personal information.', True),
                ('Privacy Data Retention', 'Retain personal information for only as long as needed to fulfil its stated purposes.', True),
            ]),
        ],
    },

    # ----- GDPR -----
    'GDPR': {
        'description': 'General Data Protection Regulation (EU)',
        'industries': ['it_saas', 'banking', 'healthcare', 'insurance'],
        'clauses': [
            ('Art.5', 'Principles of Processing', 'Lawfulness, fairness, transparency, purpose limitation, minimisation', [
                ('Lawful Basis for Processing', 'Identify and document the lawful basis for every data processing activity.', True),
            ]),
            ('Art.6-7', 'Consent Management', 'Conditions for consent', [
                ('Consent Management', 'Obtain, record, and manage explicit consent from data subjects where consent is the lawful basis.', True),
                ('Consent Withdrawal Mechanism', 'Provide a clear and simple mechanism for data subjects to withdraw consent at any time.', True),
            ]),
            ('Art.12-23', 'Data Subject Rights', 'Transparency and rights of the data subject', [
                ('Right of Access', 'Provide data subjects with access to their personal data and processing information upon request.', True),
                ('Right to Erasure', 'Erase personal data without undue delay when requested and legally permissible.', True),
                ('Data Portability', 'Provide personal data in a structured, commonly used, machine-readable format upon request.', True),
            ]),
            ('Art.33-34', 'Data Breach Notification', 'Breach notification to authorities and data subjects', [
                ('Data Breach Notification', 'Notify the supervisory authority within 72 hours of becoming aware of a personal data breach.', True),
                ('Data Subject Breach Communication', 'Communicate a high-risk breach to affected data subjects without undue delay.', True),
            ]),
            ('Art.35', 'Data Protection Impact Assessment', 'DPIA requirements', [
                ('Privacy Impact Assessment', 'Conduct a DPIA before processing that is likely to result in high risk to individuals.', True),
            ]),
            ('Art.37-39', 'Data Protection Officer', 'DPO designation and tasks', [
                ('DPO Appointment', 'Designate a Data Protection Officer where required by the nature and scale of processing.', True),
            ]),
        ],
    },

    # ----- PCI DSS -----
    'PCI DSS': {
        'description': 'Payment Card Industry Data Security Standard',
        'industries': ['banking', 'it_saas'],
        'clauses': [
            ('Req.1', 'Firewall Configuration', 'Install and maintain a firewall configuration', [
                ('Firewall Configuration', 'Install and maintain network firewalls to protect cardholder data environments.', True),
                ('DMZ Architecture', 'Establish a DMZ to limit inbound traffic to only necessary system components.', True),
            ]),
            ('Req.3', 'Cardholder Data Protection', 'Protect stored cardholder data', [
                ('Cardholder Data Protection', 'Keep cardholder data storage to a minimum and purge data that exceeds defined retention.', True),
                ('PAN Masking', 'Mask the primary account number when displayed so only authorised personnel see the full PAN.', True),
            ]),
            ('Req.4', 'Encryption in Transit', 'Encrypt transmission of cardholder data across open networks', [
                ('Encryption of Data in Transit', 'Use strong cryptography and security protocols to safeguard cardholder data during transmission.', True),
            ]),
            ('Req.7', 'Access Control', 'Restrict access to cardholder data by business need to know', [
                ('Role-Based Access Control', 'Limit access to system components and cardholder data to individuals whose jobs require such access.', True),
            ]),
            ('Req.10', 'Network Monitoring and Testing', 'Track and monitor all access to cardholder data', [
                ('Audit Logging', 'Implement automated audit trails for all system components to reconstruct security-relevant events.', True),
                ('Network Monitoring', 'Regularly test security systems and processes including vulnerability scans and penetration tests.', True),
            ]),
        ],
    },

    # ----- HIPAA -----
    'HIPAA': {
        'description': 'Health Insurance Portability and Accountability Act',
        'industries': ['healthcare'],
        'clauses': [
            ('164.312(a)', 'Access Controls', 'Technical safeguards for access', [
                ('Unique User Identification', 'Assign a unique name or number for identifying and tracking user identity.', True),
                ('Emergency Access Procedure', 'Establish procedures for obtaining necessary ePHI during an emergency.', True),
                ('Automatic Logoff', 'Implement electronic procedures that terminate sessions after a predetermined period of inactivity.', True),
            ]),
            ('164.312(b)', 'Audit Controls', 'Mechanisms to record and examine activity', [
                ('Audit Controls', 'Implement hardware, software, and procedural mechanisms to record and examine access to ePHI.', True),
            ]),
            ('164.312(c)', 'Integrity Controls', 'Protect ePHI from alteration or destruction', [
                ('PHI Integrity Mechanism', 'Implement electronic mechanisms to corroborate that ePHI has not been altered or destroyed.', True),
            ]),
            ('164.312(d)', 'Person or Entity Authentication', 'Verify identity of persons seeking access', [
                ('Authentication of Users', 'Implement procedures to verify that a person or entity seeking access to ePHI is who they claim to be.', True),
            ]),
            ('164.312(e)', 'Transmission Security', 'Guard against unauthorised access during transmission', [
                ('Transmission Security', 'Implement technical security measures to guard against unauthorised access to ePHI being transmitted.', True),
                ('PHI Encryption', 'Implement a mechanism to encrypt ePHI whenever deemed appropriate.', True),
            ]),
            ('164.308', 'Administrative Safeguards', 'Administrative actions, policies, and procedures', [
                ('PHI Protection Policy', 'Implement policies and procedures to prevent, detect, contain, and correct security violations.', True),
                ('Security Awareness Training', 'Implement a security awareness and training programme for all members of the workforce.', True),
            ]),
        ],
    },

    # ----- RBI Guidelines -----
    'RBI Cyber Security Framework': {
        'description': 'Reserve Bank of India Cyber Security Framework for Banks',
        'industries': ['banking'],
        'clauses': [
            ('RBI-1', 'IT Governance', 'IT governance structure and responsibilities', [
                ('IT Governance Framework', 'Establish IT governance framework with clearly defined roles, responsibilities, and accountability.', True),
                ('IT Strategy Committee', 'Constitute an IT Strategy Committee at the board level to oversee IT governance.', True),
            ]),
            ('RBI-2', 'Cyber Security Policy', 'Distinct cyber security policy', [
                ('Cyber Security Policy', 'Formulate a separate cyber security policy distinct from the broader IT policy.', True),
                ('Cyber Security Operations Centre', 'Set up and operationalize a Cyber Security Operations Centre (C-SOC).', True),
            ]),
            ('RBI-3', 'IS Audit', 'Information Systems Audit', [
                ('IS Audit Planning', 'Conduct a comprehensive IS Audit at least annually and after significant system changes.', True),
                ('Vulnerability Assessment and Penetration Testing', 'Conduct VAPT at least once a year and after significant infrastructure changes.', True),
            ]),
        ],
    },

    # ----- DPDP (India Digital Personal Data Protection) -----
    'DPDP Act 2023': {
        'description': 'India Digital Personal Data Protection Act 2023',
        'industries': ['it_saas', 'banking', 'healthcare', 'insurance'],
        'clauses': [
            ('Sec.4', 'Lawful Processing', 'Grounds for processing personal data', [
                ('Lawful Data Processing', 'Process personal data only for a lawful purpose for which the individual has given consent.', True),
            ]),
            ('Sec.6', 'Consent Requirements', 'Free, specific, informed, unconditional, unambiguous consent', [
                ('Consent Collection', 'Obtain free, specific, informed, unconditional, and unambiguous consent before processing personal data.', True),
                ('Consent Manager Integration', 'Enable data principals to manage consent through an accessible and transparent mechanism.', True),
            ]),
            ('Sec.8-10', 'Data Fiduciary Obligations', 'Obligations of the data fiduciary', [
                ('Data Fiduciary Obligations', 'Maintain accuracy and completeness of personal data; protect data using reasonable security safeguards.', True),
                ('Data Retention Limitation', 'Cease to retain personal data once the purpose for which it was collected has been met.', True),
                ('Grievance Redressal', 'Establish an effective mechanism for grievance redressal of data principals.', True),
            ]),
        ],
    },
}


GUIDELINE_DATA = {
    'it_saas': [
        ('Acceptable Use Policy', 'Define acceptable use of IT resources for all employees and contractors.', 'policy'),
        ('Incident Response Plan', 'Document and rehearse a structured incident response plan covering detection, containment, eradication, and recovery.', 'policy'),
        ('Secure SDLC Practices', 'Integrate security into every phase of the software development lifecycle including code reviews and SAST/DAST.', 'practice'),
        ('Vulnerability Disclosure Program', 'Establish a responsible vulnerability disclosure programme or bug bounty.', 'practice'),
        ('Third-Party Risk Management', 'Assess and monitor security posture of all third-party vendors and service providers.', 'practice'),
    ],
    'banking': [
        ('Customer Data Protection Policy', 'Establish comprehensive policies to protect customer financial and personal data.', 'policy'),
        ('Anti-Money Laundering Controls', 'Implement AML transaction monitoring and KYC verification processes.', 'policy'),
        ('Business Continuity for Core Banking', 'Maintain tested business continuity plans for core banking systems with defined RTO/RPO.', 'policy'),
        ('Fraud Detection Mechanisms', 'Deploy real-time fraud detection systems leveraging behavioural analytics.', 'practice'),
        ('Cyber Security Awareness for Staff', 'Conduct regular cyber security awareness and phishing simulation exercises for all staff.', 'practice'),
    ],
    'healthcare': [
        ('Patient Data Privacy Policy', 'Establish clear policies governing the collection, use, and disclosure of patient health information.', 'policy'),
        ('Clinical System Access Control', 'Implement role-based access to EHR and other clinical systems with audit logging.', 'policy'),
        ('Medical Device Security', 'Assess and manage cyber security risks of connected medical devices.', 'practice'),
        ('Telemedicine Security Standards', 'Define security and privacy standards for telemedicine and remote patient monitoring platforms.', 'practice'),
        ('PHI Breach Response Protocol', 'Maintain a documented protocol for responding to breaches of protected health information.', 'policy'),
    ],
    'insurance': [
        ('Policyholder Data Protection', 'Safeguard policyholder personally identifiable information in accordance with regulatory requirements.', 'policy'),
        ('Claims Processing Integrity', 'Ensure integrity and accuracy of claims processing systems with appropriate validation controls.', 'practice'),
        ('Underwriting Data Security', 'Protect underwriting data and actuarial models from unauthorized access and tampering.', 'practice'),
        ('Regulatory Reporting Controls', 'Implement controls to ensure timely and accurate regulatory reporting.', 'policy'),
        ('Third-Party Administrator Oversight', 'Monitor and audit third-party administrators handling policyholder data or claims.', 'practice'),
    ],
    'government': [
        ('Data Sovereignty Policy', 'Ensure all citizen data is stored and processed within the jurisdiction as required by law.', 'policy'),
        ('Secure Communication Standards', 'Mandate encrypted communication channels for all inter-departmental and external communications.', 'policy'),
        ('Access Governance for Public Systems', 'Implement strict access governance with MFA for all government-facing systems.', 'policy'),
        ('Citizen Data Privacy Framework', 'Establish a privacy framework governing the collection and use of citizen personal data.', 'practice'),
        ('Open Data Security Review', 'Review datasets for sensitive information before publishing under open data initiatives.', 'practice'),
    ],
}


def load_frameworks_for_org(organization):
    """
    Create ComplianceFramework, Clause, and Control records for the given
    organization based on its industry.  Also seeds Guideline records for
    the industry (idempotent -- skips if guidelines already exist).
    """
    industry = organization.industry

    for fw_name, fw_info in FRAMEWORK_DATA.items():
        if industry not in fw_info['industries']:
            continue

        framework, _ = ComplianceFramework.objects.get_or_create(
            name=fw_name,
            industry=industry,
            defaults={'description': fw_info['description']},
        )

        for clause_number, clause_title, clause_desc, controls in fw_info['clauses']:
            clause, _ = Clause.objects.get_or_create(
                framework=framework,
                number=clause_number,
                defaults={'title': clause_title, 'description': clause_desc},
            )

            for ctrl_title, ctrl_desc, mandatory in controls:
                Control.objects.get_or_create(
                    title=ctrl_title,
                    clause=clause,
                    framework=framework,
                    organization=organization,
                    defaults={
                        'description': ctrl_desc,
                        'is_mandatory': mandatory,
                    },
                )

    # Seed guidelines for the industry
    for gl_title, gl_desc, gl_cat in GUIDELINE_DATA.get(industry, []):
        Guideline.objects.get_or_create(
            industry=industry,
            title=gl_title,
            defaults={'description': gl_desc, 'category': gl_cat},
        )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
def control_list(request):
    """List all controls for the user's organisation with compliance percentage."""
    org = request.user.organization
    if org is None:
        messages.warning(request, 'You are not associated with an organisation.')
        return render(request, 'compliance/control_list.html', {
            'controls': Control.objects.none(),
            'frameworks': ComplianceFramework.objects.none(),
            'compliance_pct': 0,
            'selected_framework': None,
        })

    controls = Control.objects.filter(organization=org).select_related('clause', 'framework')
    frameworks = ComplianceFramework.objects.filter(controls__organization=org).distinct()

    selected_framework = request.GET.get('framework')
    if selected_framework:
        controls = controls.filter(framework_id=selected_framework)

    total = controls.count()
    with_docs = controls.filter(documents__isnull=False).distinct().count()
    compliance_pct = round((with_docs / total) * 100) if total else 0

    return render(request, 'compliance/control_list.html', {
        'controls': controls,
        'frameworks': frameworks,
        'compliance_pct': compliance_pct,
        'selected_framework': selected_framework,
        'total_controls': total,
        'mapped_controls': with_docs,
    })


@login_required
def control_detail(request, pk):
    """Show a single control with linked documents and risks."""
    control = get_object_or_404(Control, pk=pk, organization=request.user.organization)
    documents = control.documents.all()
    # Risks may be linked if the risks app defines a ForeignKey to Control
    risks = []
    if hasattr(control, 'risks'):
        risks = control.risks.all()

    return render(request, 'compliance/control_detail.html', {
        'control': control,
        'documents': documents,
        'risks': risks,
    })


@login_required
def document_list(request):
    """List documents for the user's organisation."""
    org = request.user.organization
    if org is None:
        documents = Document.objects.none()
    else:
        documents = Document.objects.filter(organization=org).select_related('uploaded_by')
    return render(request, 'compliance/document_list.html', {
        'documents': documents,
    })


@login_required
def document_upload(request):
    """Upload a document and map it to controls."""
    org = request.user.organization
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, organization=org)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.organization = org
            doc.uploaded_by = request.user
            doc.save()
            form.save_m2m()
            # Calculate and store checksums
            from .utils import calculate_checksums
            sha256, md5 = calculate_checksums(doc.file)
            doc.checksum_sha256 = sha256
            doc.checksum_md5 = md5
            doc.file_size = doc.file.size
            doc.save()
            messages.success(request, f'Document "{doc.title}" uploaded successfully.')
            return redirect('compliance:document_detail', pk=doc.pk)
    else:
        form = DocumentForm(organization=org)
    return render(request, 'compliance/document_upload.html', {
        'form': form,
    })


@login_required
def document_detail(request, pk):
    """Show document details with control mapping and compliance impact."""
    doc = get_object_or_404(Document, pk=pk, organization=request.user.organization)
    mapped_controls = doc.controls.select_related('clause', 'framework')

    # Compliance impact: how many total controls in the org now have at least one document
    org = request.user.organization
    total_controls = Control.objects.filter(organization=org).count()
    controls_with_docs = Control.objects.filter(organization=org, documents__isnull=False).distinct().count()
    compliance_pct = round((controls_with_docs / total_controls) * 100) if total_controls else 0

    return render(request, 'compliance/document_detail.html', {
        'document': doc,
        'mapped_controls': mapped_controls,
        'compliance_pct': compliance_pct,
        'total_controls': total_controls,
        'controls_with_docs': controls_with_docs,
    })


@login_required
def verify_document(request, pk):
    """Verify document checksum integrity."""
    document = get_object_or_404(Document, pk=pk, organization=request.user.organization)
    from .utils import verify_document_checksum
    is_valid, message = verify_document_checksum(document)
    if is_valid:
        document.is_verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.save()
        messages.success(request, message)
    else:
        document.is_verified = False
        document.save()
        messages.error(request, message)
    return redirect('compliance:document_detail', pk=pk)


@login_required
def guideline_list(request):
    """Show industry-specific guidelines based on the user's org industry."""
    org = request.user.organization
    if org is None:
        guidelines = Guideline.objects.none()
        industry_display = ''
    else:
        guidelines = Guideline.objects.filter(industry=org.industry)
        industry_display = org.get_industry_display()
    return render(request, 'compliance/guideline_list.html', {
        'guidelines': guidelines,
        'industry_display': industry_display,
    })
