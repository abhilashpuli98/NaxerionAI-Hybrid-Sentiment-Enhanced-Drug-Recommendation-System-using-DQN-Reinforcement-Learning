"""PDF Report Generator for SEDRS System"""

from fpdf import FPDF
from datetime import datetime
import os


class SEDRSReport(FPDF):
    """Custom PDF report for SEDRS analysis results"""
    
    def sanitize_text(self, text):
        """Sanitize text to handle unsupported characters for Latin-1 encoding"""
        if not text:
            return ""
        replacements = {
            '\u2013': '-',   # en-dash
            '\u2014': '--',  # em-dash
            '\u2018': "'",   # left single quote
            '\u2019': "'",   # right single quote
            '\u201c': '"',   # left double quote
            '\u201d': '"',   # right double quote
            '\u2022': '*',   # bullet
            '•': '*',        # other bullet
            '…': '...'       # ellipsis
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Final fallback: encode to latin-1, replace errors
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(79, 70, 229)  # Primary color
        self.cell(0, 10, "Naxerion AI's - SEDRS Analysis Report", align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font('Helvetica', '', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 6, 'Sentiment-Enhanced Drug Recommendation System', align='C', new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | Page {self.page_no()}', align='C')


def generate_report(patient, interaction, recommendations):
    """Generate a PDF report for a given interaction and its recommendations.
    
    Args:
        patient: Patient model instance
        interaction: Interaction model instance
        recommendations: List of Recommendation model instances
    
    Returns:
        bytes: The PDF content as bytes
    """
    pdf = SEDRSReport()
    pdf.add_page()
    
    # --- Patient Information ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, 'Patient Information', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    
    info_data = [
        ('Patient ID', str(patient.id)),
        ('Email', pdf.sanitize_text(patient.email) or 'N/A'),
        ('Age', str(patient.age) if patient.age else 'N/A'),
        ('Gender', {'M': 'Male', 'F': 'Female', 'O': 'Other'}.get(patient.gender, 'N/A')),
        ('Medical Conditions', pdf.sanitize_text(patient.medical_conditions) or 'None reported'),
        ('Allergies', pdf.sanitize_text(patient.allergies) or 'None reported'),
    ]
    
    for label, value in info_data:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(50, 7, f'{label}:', new_x="RIGHT")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    
    # --- Analysis Summary ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, 'Analysis Summary', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    
    analysis_data = [
        ('Interaction ID', str(interaction.id)),
        ('Date', interaction.created_at.strftime('%B %d, %Y at %H:%M') if interaction.created_at else 'N/A'),
        ('Condition Detected', pdf.sanitize_text(interaction.condition) or 'Not detected'),
        ('Sentiment', pdf.sanitize_text(interaction.sentiment_label or 'N/A').capitalize()),
        ('Sentiment Score', f'{interaction.sentiment_score:.4f}' if interaction.sentiment_score else 'N/A'),
        ('Overall Confidence', f'{(interaction.overall_confidence or 0) * 100:.1f}%'),
    ]
    
    for label, value in analysis_data:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(50, 7, f'{label}:', new_x="RIGHT")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
    
    if interaction.text_input:
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, 'Patient Description:', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, pdf.sanitize_text(interaction.text_input))
    
    pdf.ln(5)
    
    # --- Drug Recommendations Table ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, pdf.sanitize_text(f'Drug Recommendations ({len(recommendations)} found)'), new_x="LMARGIN", new_y="NEXT")
    
    if recommendations:
        # Table header
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(71, 85, 105)
        
        col_widths = [15, 55, 35, 35, 35]
        headers = ['Rank', 'Drug Name', 'Score', 'Efficacy', 'Sentiment']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
        pdf.ln()
        
        # Table body
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(30, 41, 59)
        
        for rec in recommendations:
            pdf.cell(col_widths[0], 7, f'#{rec.rank}', border=1, align='C')
            pdf.cell(col_widths[1], 7, pdf.sanitize_text(rec.drug_name or 'N/A'), border=1)
            pdf.cell(col_widths[2], 7, f'{rec.composite_score:.4f}' if rec.composite_score else 'N/A', border=1, align='C')
            pdf.cell(col_widths[3], 7, f'{(rec.efficacy_score or 0) * 100:.1f}%', border=1, align='C')
            pdf.cell(col_widths[4], 7, f'{rec.sentiment_score:.4f}' if rec.sentiment_score else 'N/A', border=1, align='C')
            pdf.ln()
            
        # Disclaimer about content
        if any(rec.drug_name == 'EMERGENCY' for rec in recommendations):
             pdf.set_text_color(220, 53, 69)
             pdf.multi_cell(0, 10, "CRITICAL WARNING: The analyzed condition appears to be a medical emergency. Please seek immediate professional medical attention.")
             pdf.set_text_color(30, 41, 59)

    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, 'No recommendations were generated for this analysis.', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(8)
    
    # --- Disclaimer ---
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 5, 
        'DISCLAIMER: This report is generated by an AI system for informational purposes only. '
        'It does not constitute medical advice. Always consult a qualified healthcare professional '
        'before making any medical decisions. SEDRS - Publication-Grade Multi-Modal Healthcare AI.')
    
    return pdf.output()

def generate_full_patient_report(patient, interactions):
    """Generate a comprehensive PDF report for a patient's entire history.
    
    Args:
        patient: Patient model instance
        interactions: List of Interaction model instances
    
    Returns:
        bytes: The PDF content as bytes
    """
    pdf = SEDRSReport()
    pdf.add_page()
    
    # --- Patient Information ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f'Patient History Report: {pdf.sanitize_text(patient.email)}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    
    info_data = [
        ('Patient ID', str(patient.id)),
        ('Date Joined', patient.created_at.strftime('%B %d, %Y')),
        ('Total Interactions', str(len(interactions))),
        ('Age', str(patient.age) if patient.age else 'N/A'),
        ('Gender', {'M': 'Male', 'F': 'Female', 'O': 'Other'}.get(patient.gender, 'N/A')),
    ]
    
    for label, value in info_data:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 7, f'{label}:', new_x="RIGHT")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    
    # --- Interaction History ---
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, 'Interaction History', new_x="LMARGIN", new_y="NEXT")
    
    if not interactions:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, 'No interactions recorded.', new_x="LMARGIN", new_y="NEXT")
    else:
        # Table header
        pdf.set_fill_color(248, 250, 252)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(71, 85, 105)
        
        # Date, Condition, Confidence, Top Recommendation
        col_widths = [40, 50, 25, 75]
        headers = ['Date', 'Condition', 'Conf.', 'Top Recommendation']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
        pdf.ln()
        
        # Table body
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(30, 41, 59)
        
        for interaction in interactions:
            # Get top recommendation if available
            top_drug = "N/A"
            if interaction.recommendations:
                # Assuming recommendations are already sorted or we just take the first one
                top_drug = interaction.recommendations[0].drug_name
            
            # Check for page break
            if pdf.get_y() > 270:
                pdf.add_page()
                # Re-print header
                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_fill_color(248, 250, 252)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
                pdf.ln()
                pdf.set_font('Helvetica', '', 9)

            date_str = interaction.created_at.strftime('%Y-%m-%d %H:%M')
            condition = pdf.sanitize_text(interaction.condition or 'Unknown')
            confidence = f"{(interaction.overall_confidence or 0)*100:.0f}%"
            top_drug = pdf.sanitize_text(top_drug)
            
            pdf.cell(col_widths[0], 7, date_str, border=1)
            pdf.cell(col_widths[1], 7, condition, border=1)
            pdf.cell(col_widths[2], 7, confidence, border=1, align='C')
            pdf.cell(col_widths[3], 7, top_drug, border=1)
            pdf.ln()
            
    pdf.ln(8)
    
    # --- Disclaimer ---
    pdf.set_y(-30)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 5, 
        'DISCLAIMER: This report is generated by an AI system for administrative use. '
        'SEDRS - Publication-Grade Multi-Modal Healthcare AI.')
    
    return pdf.output()
