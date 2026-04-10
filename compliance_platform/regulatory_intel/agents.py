"""
Multi-Agent Regulatory Intelligence System
==========================================
Agents:
  1. Monitor Agent   – Watches regulatory sources for new content
  2. Scraper Agent   – Downloads and extracts text from PDFs/HTML
  3. Diff Agent      – Computes clause-level diffs between old and new
  4. Classifier Agent – Categorizes changes (KYC, prudential, cyber, etc.)
  5. Mapper Agent    – Maps changes to products/departments/policies
  6. Drafter Agent   – Generates policy amendment drafts via LLM
  7. Reporter Agent  – Assembles final impact report
"""

import difflib
import json
import logging
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword ontology for mapping regulations to compliance categories
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    'kyc_aml': [
        'KYC', 'know your customer', 'AML', 'anti-money laundering', 'PMLA',
        'customer due diligence', 'CDD', 'suspicious transaction', 'STR', 'CTR',
        'FIU', 'beneficial owner', 'PEP', 'politically exposed', 'CKYC',
        'identity verification', 'Aadhaar', 'e-KYC',
    ],
    'prudential_norms': [
        'capital adequacy', 'CRAR', 'CRR', 'SLR', 'Basel', 'NPA',
        'provisioning', 'IRAC', 'asset classification', 'risk weight',
        'large exposure', 'ALM', 'liquidity', 'dividend', 'profit distribution',
    ],
    'reporting': [
        'return', 'filing', 'disclosure', 'supervisory', 'report', 'FEMA return',
        'FLA', 'ECB return', 'quarterly report', 'annual return',
    ],
    'cybersecurity': [
        'cyber', 'cybersecurity', 'information security', 'CERT-In', 'CISO',
        'IT outsourcing', 'cloud', 'data breach', 'incident reporting',
        'penetration testing', 'vulnerability', 'ransomware',
    ],
    'digital_payments': [
        'UPI', 'NEFT', 'RTGS', 'IMPS', 'payment aggregator', 'PPI',
        'prepaid', 'tokenization', 'card', 'mobile banking', 'QR code',
        'digital lending', 'NPCI', 'e-mandate',
    ],
    'customer_protection': [
        'fair practice', 'ombudsman', 'grievance', 'customer service',
        'transparency', 'charges', 'interest rate', 'MCLR', 'EBLR',
        'borrower rights', 'cooling off period',
    ],
    'lending_npa': [
        'loan', 'lending', 'credit', 'NPA', 'restructuring', 'write-off',
        'recovery', 'SARFAESI', 'IBC', 'insolvency', 'wilful defaulter',
        'priority sector', 'PSL', 'MSME', 'microfinance', 'housing loan',
    ],
    'fema_forex': [
        'FEMA', 'foreign exchange', 'LRS', 'liberalised remittance',
        'ODI', 'FDI', 'ECB', 'external commercial borrowing',
        'nostro', 'vostro', 'NRI', 'NRO', 'NRE', 'FPI', 'authorized dealer',
        'forex', 'cross-border', 'remittance', 'trade finance', 'export credit',
    ],
}

ENTITY_KEYWORDS = {
    'banks': ['bank', 'scheduled commercial bank', 'SCB', 'public sector bank', 'private bank'],
    'nbfcs': ['NBFC', 'non-banking financial', 'housing finance', 'microfinance institution'],
    'fintechs': ['fintech', 'digital lending', 'payment aggregator', 'neo-bank', 'tech'],
    'corporates': ['company', 'corporate', 'listed entity', 'MCA', 'board of directors'],
    'cooperative_banks': ['co-operative bank', 'UCB', 'urban cooperative', 'state cooperative'],
    'insurers': ['insurance', 'IRDAI', 'insurer', 'policyholder'],
    'fpis': ['FPI', 'foreign portfolio', 'foreign institutional'],
}


# ---------------------------------------------------------------------------
# 1. MONITOR AGENT
# ---------------------------------------------------------------------------
class MonitorAgent:
    """Monitors regulatory source pages for new content."""

    RBI_NOTIFICATIONS_URL = 'https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx'
    RBI_CIRCULARS_URL = 'https://www.rbi.org.in/Scripts/NotificationUser.aspx'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (ComplianceBot/1.0; regulatory-monitoring)'
        })

    def check_rbi_notifications(self):
        """Scrape RBI notifications page for new circulars."""
        results = []
        try:
            resp = self.session.get(self.RBI_CIRCULARS_URL, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            # RBI notifications table rows
            table = soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_gvNotification'})
            if not table:
                # Try alternative selectors
                tables = soup.find_all('table', class_='tablebg')
                table = tables[0] if tables else None

            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:20]:  # Latest 20
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        link_tag = cols[1].find('a')
                        title = link_tag.get_text(strip=True) if link_tag else cols[1].get_text(strip=True)
                        href = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''
                        date_str = cols[0].get_text(strip=True)
                        ref_no = cols[2].get_text(strip=True) if len(cols) > 2 else ''

                        results.append({
                            'title': title,
                            'date': date_str,
                            'reference': ref_no,
                            'url': f'https://www.rbi.org.in/Scripts/{href}' if href and not href.startswith('http') else href,
                            'source': 'rbi',
                        })
            logger.info(f"MonitorAgent: Found {len(results)} RBI notifications")
        except Exception as e:
            logger.error(f"MonitorAgent: Error scraping RBI: {e}")

        return results

    def check_sebi_circulars(self):
        """Scrape SEBI circulars page."""
        results = []
        try:
            resp = self.session.get('https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=2', timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            items = soup.find_all('li', class_='list-item')
            for item in items[:20]:
                link_tag = item.find('a')
                date_tag = item.find('span', class_='list-date')
                if link_tag:
                    results.append({
                        'title': link_tag.get_text(strip=True),
                        'url': link_tag.get('href', ''),
                        'date': date_tag.get_text(strip=True) if date_tag else '',
                        'source': 'sebi',
                    })
            logger.info(f"MonitorAgent: Found {len(results)} SEBI circulars")
        except Exception as e:
            logger.error(f"MonitorAgent: Error scraping SEBI: {e}")

        return results


# ---------------------------------------------------------------------------
# 2. SCRAPER AGENT
# ---------------------------------------------------------------------------
class ScraperAgent:
    """Downloads documents and extracts text from PDFs/HTML."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (ComplianceBot/1.0; regulatory-monitoring)'
        })

    def download_and_extract(self, url):
        """Download a regulatory document and extract text."""
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            content_type = resp.headers.get('Content-Type', '')

            if 'pdf' in content_type.lower() or url.lower().endswith('.pdf'):
                return self._extract_from_pdf(resp.content)
            else:
                return self._extract_from_html(resp.text)
        except Exception as e:
            logger.error(f"ScraperAgent: Error downloading {url}: {e}")
            return ''

    def _extract_from_pdf(self, pdf_bytes):
        """Extract text from PDF using PyMuPDF."""
        try:
            import pymupdf
            doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"ScraperAgent: PDF extraction error: {e}")
            return ''

    def _extract_from_html(self, html_content):
        """Extract meaningful text from HTML page."""
        soup = BeautifulSoup(html_content, 'lxml')
        # Remove script and style elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        # Get text from main content area
        main = soup.find('div', {'id': 'content'}) or soup.find('main') or soup.find('body')
        if main:
            return main.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)


# ---------------------------------------------------------------------------
# 3. DIFF AGENT
# ---------------------------------------------------------------------------
class DiffAgent:
    """Computes clause-level differences between regulation versions."""

    @staticmethod
    def compute_text_diff(old_text, new_text):
        """Compute unified diff between old and new text."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile='Previous Version',
            tofile='New Version',
            lineterm=''
        ))
        return diff

    @staticmethod
    def extract_clause_changes(old_text, new_text):
        """Extract structured clause-level changes."""
        changes = []

        # Split into sections/clauses
        old_sections = DiffAgent._split_into_sections(old_text)
        new_sections = DiffAgent._split_into_sections(new_text)

        all_keys = set(list(old_sections.keys()) + list(new_sections.keys()))

        for key in sorted(all_keys):
            old_content = old_sections.get(key, '')
            new_content = new_sections.get(key, '')

            if old_content and not new_content:
                changes.append({
                    'clause': key,
                    'type': 'removed',
                    'old_text': old_content,
                    'new_text': '',
                    'summary': f'Clause {key} has been removed.',
                })
            elif new_content and not old_content:
                changes.append({
                    'clause': key,
                    'type': 'added',
                    'old_text': '',
                    'new_text': new_content,
                    'summary': f'New clause {key} has been added.',
                })
            elif old_content != new_content:
                # Compute similarity ratio
                ratio = difflib.SequenceMatcher(None, old_content, new_content).ratio()
                changes.append({
                    'clause': key,
                    'type': 'modified',
                    'old_text': old_content,
                    'new_text': new_content,
                    'similarity': round(ratio, 2),
                    'summary': f'Clause {key} modified (similarity: {ratio:.0%}).',
                })

        return changes

    @staticmethod
    def _split_into_sections(text):
        """Split regulatory text into sections by heading patterns."""
        sections = {}
        # Match patterns like "Section 5", "Clause 3.2", "Chapter IV", "(a)", "1.", etc.
        pattern = re.compile(
            r'^(?:'
            r'(?:Section|Sec\.?|Clause|Chapter|Article|Part|Schedule|Appendix|Annex)\s+[\w\.\-]+|'
            r'\d+[\.\)]\s|'
            r'\([a-z]\)|'
            r'[IVXLC]+\.'
            r')',
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(pattern.finditer(text))
        if not matches:
            sections['Full Document'] = text
            return sections

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            key = match.group().strip().rstrip('.')
            content = text[start:end].strip()
            sections[key] = content

        return sections

    @staticmethod
    def generate_diff_html(old_text, new_text):
        """Generate an HTML diff view for the UI."""
        differ = difflib.HtmlDiff(wrapcolumn=80)
        return differ.make_table(
            old_text.splitlines(),
            new_text.splitlines(),
            fromdesc='Previous Version',
            todesc='New Version',
            context=True,
            numlines=3,
        )


# ---------------------------------------------------------------------------
# 4. CLASSIFIER AGENT
# ---------------------------------------------------------------------------
class ClassifierAgent:
    """Classifies regulatory changes into compliance categories."""

    @staticmethod
    def classify_document(text, title=''):
        """Classify a regulatory document into categories."""
        combined = f"{title} {text}".lower()
        categories = []
        scores = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                count = combined.count(keyword.lower())
                score += count
            if score > 0:
                scores[category] = score
                categories.append(category)

        # Sort by relevance
        categories.sort(key=lambda c: scores.get(c, 0), reverse=True)
        return categories

    @staticmethod
    def classify_entities(text, title=''):
        """Identify which entities are affected."""
        combined = f"{title} {text}".lower()
        entities = []

        for entity, keywords in ENTITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in combined:
                    entities.append(entity)
                    break

        return entities

    @staticmethod
    def assess_impact(text, title=''):
        """Heuristic impact assessment based on keywords."""
        combined = f"{title} {text}".lower()
        score = 0

        # High-impact indicators
        high_impact = ['mandatory', 'shall', 'must', 'penalty', 'fine', 'imprisonment',
                       'effective immediately', 'with immediate effect', 'prohibition',
                       'ban', 'restrict', 'suspend', 'cancel', 'revoke']
        for word in high_impact:
            if word in combined:
                score += 3

        # Medium-impact indicators
        medium_impact = ['may', 'should', 'recommend', 'guideline', 'advisory',
                         'clarification', 'amendment', 'revision', 'update']
        for word in medium_impact:
            if word in combined:
                score += 1

        # Timeline urgency
        urgency_words = ['immediate', 'forthwith', 'within 30 days', 'urgent', 'emergency']
        for word in urgency_words:
            if word in combined:
                score += 2

        if score >= 15:
            return 'critical'
        elif score >= 8:
            return 'high'
        elif score >= 4:
            return 'medium'
        return 'low'


# ---------------------------------------------------------------------------
# 5. MAPPER AGENT
# ---------------------------------------------------------------------------
class MapperAgent:
    """Maps regulatory changes to company products/departments/policies."""

    PRODUCT_MAPPING = {
        'kyc_aml': {
            'departments': ['KYC/AML Compliance', 'Retail Banking', 'Branch Operations'],
            'products': ['Savings Accounts', 'Current Accounts', 'Fixed Deposits', 'Loans'],
            'policies': ['KYC Policy', 'AML Policy', 'Customer Acceptance Policy'],
            'systems': ['CBS (Core Banking)', 'KYC Verification System', 'Transaction Monitoring'],
        },
        'prudential_norms': {
            'departments': ['Risk Management', 'Treasury', 'Finance/Accounts'],
            'products': ['All Lending Products', 'Investment Portfolio', 'Capital Instruments'],
            'policies': ['Credit Policy', 'ALM Policy', 'Capital Management Policy'],
            'systems': ['Risk Management System', 'Treasury Management', 'Regulatory Reporting'],
        },
        'cybersecurity': {
            'departments': ['IT Security', 'CISO Office', 'IT Operations'],
            'products': ['Internet Banking', 'Mobile Banking', 'API Services'],
            'policies': ['Information Security Policy', 'IT Outsourcing Policy', 'BCP/DR Policy'],
            'systems': ['Firewall/IDS', 'SIEM', 'Cloud Infrastructure', 'Endpoint Security'],
        },
        'digital_payments': {
            'departments': ['Digital Banking', 'Payments Operations', 'Card Operations'],
            'products': ['UPI', 'Mobile Banking', 'Debit/Credit Cards', 'Net Banking', 'PPI/Wallets'],
            'policies': ['Payments Policy', 'Card Issuance Policy', 'Digital Lending Policy'],
            'systems': ['Payment Gateway', 'UPI Switch', 'Card Management System'],
        },
        'fema_forex': {
            'departments': ['Forex/Treasury', 'Trade Finance', 'NRI Services'],
            'products': ['Export Credit', 'Import Finance', 'Forex Trading', 'NRI Accounts', 'ECB'],
            'policies': ['FEMA Compliance Policy', 'Trade Finance Policy', 'LRS Policy'],
            'systems': ['Forex Trading Platform', 'Trade Finance Module', 'FEMA Reporting System'],
        },
        'lending_npa': {
            'departments': ['Credit Department', 'Recovery/Collections', 'Risk Management'],
            'products': ['Home Loans', 'Personal Loans', 'MSME Loans', 'Corporate Loans'],
            'policies': ['Credit Policy', 'NPA Management Policy', 'Recovery Policy', 'PSL Policy'],
            'systems': ['Loan Origination System', 'Loan Management System', 'NPA Tracking'],
        },
        'customer_protection': {
            'departments': ['Customer Service', 'Compliance', 'Branch Operations'],
            'products': ['All Customer-facing Products'],
            'policies': ['Fair Practice Code', 'Grievance Redressal Policy', 'Compensation Policy'],
            'systems': ['CRM', 'Complaint Management System', 'Ombudsman Portal'],
        },
        'reporting': {
            'departments': ['Compliance', 'Finance', 'Regulatory Reporting'],
            'products': ['All Products (for data)'],
            'policies': ['Regulatory Reporting Policy', 'Disclosure Policy'],
            'systems': ['Regulatory Reporting System', 'Data Warehouse', 'MIS'],
        },
    }

    @staticmethod
    def map_to_business(categories, change_text=''):
        """Map categories to affected business areas."""
        mappings = []
        for cat in categories:
            mapping = MapperAgent.PRODUCT_MAPPING.get(cat, {})
            if mapping:
                for dept in mapping.get('departments', []):
                    mappings.append({
                        'area_type': 'department',
                        'area_name': dept,
                        'category': cat,
                    })
                for product in mapping.get('products', []):
                    mappings.append({
                        'area_type': 'product',
                        'area_name': product,
                        'category': cat,
                    })
                for policy in mapping.get('policies', []):
                    mappings.append({
                        'area_type': 'policy',
                        'area_name': policy,
                        'category': cat,
                    })
                for system in mapping.get('systems', []):
                    mappings.append({
                        'area_type': 'system',
                        'area_name': system,
                        'category': cat,
                    })
        return mappings


# ---------------------------------------------------------------------------
# 6. DRAFTER AGENT (LLM-powered)
# ---------------------------------------------------------------------------
class DrafterAgent:
    """Uses LLM to generate policy amendment drafts and action items."""

    @staticmethod
    def generate_policy_amendment(change_summary, current_policy='', regulation_text=''):
        """Generate a draft policy amendment using LLM."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))

            prompt = f"""You are a regulatory compliance expert for an Indian bank/NBFC.

Based on the following regulatory change, draft a concise policy amendment.

## Regulatory Change:
{change_summary}

## Relevant Regulation Text:
{regulation_text[:2000]}

## Current Policy (if available):
{current_policy[:1000] if current_policy else 'Not provided'}

## Instructions:
1. Draft a clear policy amendment clause that addresses the regulatory change
2. Use formal policy language
3. Include effective dates if mentioned
4. Highlight key compliance requirements
5. Keep it concise and actionable

Respond in JSON format with keys: amendment_text, key_requirements (list), effective_date, risk_level (high/medium/low)"""

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DrafterAgent LLM error: {e}")
            # Fallback: generate a template-based response
            return json.dumps({
                'amendment_text': f'Policy amendment required per regulatory change: {change_summary[:200]}',
                'key_requirements': ['Review and update relevant SOPs', 'Notify affected departments', 'Update compliance checklist'],
                'effective_date': 'As per regulatory notification',
                'risk_level': 'medium',
            })

    @staticmethod
    def generate_action_items(change_summary, affected_areas):
        """Generate specific action items for each affected area."""
        action_items = []
        for area in affected_areas:
            action_items.append({
                'area': area.get('area_name', ''),
                'type': area.get('area_type', ''),
                'action': f"Review and update {area.get('area_name', '')} in light of: {change_summary[:100]}...",
                'priority': 'high' if 'policy' in area.get('area_type', '') else 'medium',
                'status': 'pending',
            })
        return action_items


# ---------------------------------------------------------------------------
# 7. REPORTER AGENT
# ---------------------------------------------------------------------------
class ReporterAgent:
    """Assembles the final impact report."""

    @staticmethod
    def generate_report(document_data, diffs, mappings, amendments=None):
        """Generate a comprehensive impact report."""
        report = {
            'title': f"Impact Report: {document_data.get('title', 'Regulatory Change')}",
            'generated_at': datetime.now().isoformat(),
            'executive_summary': ReporterAgent._build_executive_summary(document_data, diffs),
            'detailed_analysis': ReporterAgent._build_detailed_analysis(diffs),
            'affected_areas': ReporterAgent._build_affected_areas(mappings),
            'policy_amendments': amendments or '',
            'risk_assessment': ReporterAgent._build_risk_assessment(diffs, mappings),
            'action_items': ReporterAgent._build_action_items(mappings),
            'compliance_timeline': ReporterAgent._build_timeline(document_data),
            'overall_risk_score': ReporterAgent._calculate_overall_risk(diffs, mappings),
        }
        return report

    @staticmethod
    def _build_executive_summary(doc_data, diffs):
        title = doc_data.get('title', 'N/A')
        source = doc_data.get('source', 'N/A')
        date = doc_data.get('published_date', 'N/A')
        num_changes = len(diffs) if diffs else 0

        return (
            f"A new regulatory update titled \"{title}\" has been published by {source} "
            f"on {date}. This analysis identifies {num_changes} clause-level change(s). "
            f"The following report details the nature of changes, affected business areas, "
            f"and recommended actions for compliance."
        )

    @staticmethod
    def _build_detailed_analysis(diffs):
        if not diffs:
            return "No clause-level differences detected (new document or first version)."

        analysis = []
        for diff in diffs:
            analysis.append(
                f"**{diff.get('clause', 'Unknown')}** [{diff.get('type', 'unknown').upper()}]: "
                f"{diff.get('summary', 'Change detected.')}"
            )
        return '\n\n'.join(analysis)

    @staticmethod
    def _build_affected_areas(mappings):
        if not mappings:
            return "No specific business area mappings identified."

        areas = {}
        for m in mappings:
            area_type = m.get('area_type', 'other')
            if area_type not in areas:
                areas[area_type] = []
            areas[area_type].append(m.get('area_name', ''))

        result = []
        for area_type, names in areas.items():
            result.append(f"**{area_type.title()}**: {', '.join(set(names))}")
        return '\n'.join(result)

    @staticmethod
    def _build_risk_assessment(diffs, mappings):
        if not diffs:
            return "Risk assessment pending further analysis."

        high_impact = sum(1 for d in diffs if d.get('type') == 'added' or d.get('type') == 'removed')
        modified = sum(1 for d in diffs if d.get('type') == 'modified')
        total_areas = len(set(m.get('area_name', '') for m in mappings)) if mappings else 0

        return (
            f"Changes detected: {high_impact} major (added/removed clauses), "
            f"{modified} modifications. Affecting approximately {total_areas} business areas. "
            f"Recommend immediate review by compliance team."
        )

    @staticmethod
    def _build_action_items(mappings):
        items = []
        seen = set()
        for m in (mappings or []):
            name = m.get('area_name', '')
            if name not in seen:
                seen.add(name)
                items.append(f"- Review and update {name}")
        return '\n'.join(items) if items else "No specific action items generated."

    @staticmethod
    def _build_timeline(doc_data):
        effective = doc_data.get('effective_date', 'Not specified')
        deadline = doc_data.get('compliance_deadline', 'Not specified')
        return f"Effective Date: {effective}\nCompliance Deadline: {deadline}"

    @staticmethod
    def _calculate_overall_risk(diffs, mappings):
        base = 3
        if diffs:
            base += min(len(diffs), 5)
        if mappings:
            unique_areas = len(set(m.get('area_name', '') for m in mappings))
            base += min(unique_areas // 3, 3)
        return min(base, 10)
