import * as XLSX from 'xlsx';
import { ReviewResponse } from '../types/review';

function applyAutoColumnWidths(worksheet: XLSX.WorkSheet, rows: any[][], minWidths?: { [colIndex: number]: number }) {
  const colWidths: number[] = [];
  rows.forEach((row) => {
    row.forEach((cell, colIdx) => {
      const valStr = cell !== null && cell !== undefined ? String(cell) : '';
      // Ignore main section headers in column 0 for column width calculation
      const effectiveLength = (colIdx === 0 && valStr.length > 45) ? 28 : valStr.length;
      const minW = minWidths && minWidths[colIdx] ? minWidths[colIdx] : 12;
      colWidths[colIdx] = Math.max(colWidths[colIdx] || minW, Math.min(effectiveLength + 4, 80));
    });
  });
  worksheet['!cols'] = colWidths.map((w) => ({ wch: w }));
}

export function exportWP514ToExcel(data: ReviewResponse, finalDecision?: string, finalComments?: string) {
  const wp = data.wp514;
  if (!wp) return;

  const workbook = XLSX.utils.book_new();

  // ==========================================
  // SHEET 1: EXECUTIVE SUMMARY & AUDITOR SIGN-OFF
  // ==========================================
  const s1Rows: any[][] = [];
  s1Rows.push(['WP-514 — FINANCIAL STATEMENT REVIEW WORKING PAPER']);
  s1Rows.push(['1. ENGAGEMENT / REVIEW DETAILS']);
  s1Rows.push(['WP Reference', 'WP-514 (2026)']);
  s1Rows.push(['Bank Name', wp.engagement_details.bank_name]);
  s1Rows.push(['Bank ID', wp.engagement_details.bank_id]);
  s1Rows.push(['Reporting Period', wp.engagement_details.reporting_period]);
  s1Rows.push(['Comparative Period', wp.engagement_details.comparative_period]);
  s1Rows.push(['Currency', wp.engagement_details.currency]);
  s1Rows.push(['Reporting Unit', wp.engagement_details.unit]);
  s1Rows.push(['Source Document', wp.engagement_details.source_document_current]);
  s1Rows.push(['Review Date', wp.engagement_details.review_date]);
  s1Rows.push(['Prepared By', wp.engagement_details.prepared_by]);
  s1Rows.push(['Reviewed By', wp.engagement_details.reviewed_by]);
  s1Rows.push(['Overall Review Status', wp.engagement_details.overall_status]);
  s1Rows.push([]);

  s1Rows.push(['2. FINANCIAL STATEMENT REVIEW SUMMARY']);
  s1Rows.push(['Statement Area', 'Checks Performed', 'Passed', 'Failed', 'Warnings', 'Overall Status']);
  wp.financial_statement_summary.forEach((s) => {
    s1Rows.push([s.statement, s.checks_performed, s.passed, s.failed, s.warnings, s.overall_status]);
  });
  s1Rows.push([]);

  s1Rows.push(['8. OVERALL CONCLUSION & AUDITOR SIGN-OFF']);
  s1Rows.push(['Overall Review Result', wp.overall_conclusion.overall_review_result]);
  s1Rows.push(['Total Exceptions', wp.overall_conclusion.total_exceptions]);
  s1Rows.push(['Critical Exceptions', wp.overall_conclusion.critical_exceptions]);
  s1Rows.push(['High Exceptions', wp.overall_conclusion.high_exceptions]);
  s1Rows.push(['Medium Exceptions', wp.overall_conclusion.medium_exceptions]);
  s1Rows.push(['Key Issues Requiring Attention', wp.overall_conclusion.key_issues_requiring_attention.join('; ')]);
  s1Rows.push(['AI-Generated Review Summary', wp.overall_conclusion.ai_generated_review_summary]);
  s1Rows.push(['Final Reviewer Decision', finalDecision || wp.overall_conclusion.final_reviewer_decision]);
  s1Rows.push(['Reviewer Comments', finalComments || wp.overall_conclusion.reviewer_comments]);

  const ws1 = XLSX.utils.aoa_to_sheet(s1Rows);
  applyAutoColumnWidths(ws1, s1Rows, { 0: 32, 1: 50, 2: 15, 3: 15, 4: 15, 5: 20 });
  XLSX.utils.book_append_sheet(workbook, ws1, 'Summary & Auditor Sign-off');

  // ==========================================
  // SHEET 2: DETAILED FINDINGS & EXCEPTION LOG
  // ==========================================
  const s2Rows: any[][] = [];
  s2Rows.push(['3. DETAILED REVIEW FINDINGS / EXCEPTION LOG']);
  s2Rows.push([
    'Issue ID',
    'Statement Area',
    'Module Engine',
    'Review Check',
    'Check Status',
    'Reported / Actual',
    'Expected Value',
    'Numeric Variance',
    'Severity',
    'Evidence Reference / Pointers',
    'AI Candidate Narrative Explanation',
    'Reviewer Sign-off Status',
  ]);
  data.findings.forEach((f) => {
    s2Rows.push([
      f.finding_id,
      f.statement,
      f.module,
      f.check,
      f.status.toUpperCase(),
      typeof f.actual === 'number' ? `₹${f.actual} Cr` : String(f.actual ?? '—'),
      typeof f.expected === 'number' ? `₹${f.expected} Cr` : String(f.expected ?? '—'),
      f.difference !== null && f.difference !== undefined ? (typeof f.difference === 'number' ? `₹${f.difference} Cr` : String(f.difference)) : '—',
      f.severity.toUpperCase(),
      f.evidence ? f.evidence.map((e) => `${e.table} (Page ${e.page}, Row: ${e.row})`).join('; ') : 'N/A',
      f.ai_explanation ? f.ai_explanation.text || f.ai_explanation.suggested_revision || '' : 'N/A',
      f.reviewer_status,
    ]);
  });

  const ws2 = XLSX.utils.aoa_to_sheet(s2Rows);
  applyAutoColumnWidths(ws2, s2Rows, {
    0: 12, // Issue ID
    1: 25, // Statement Area
    2: 22, // Module Engine
    3: 32, // Review Check
    4: 14, // Status
    5: 18, // Actual
    6: 18, // Expected
    7: 18, // Variance
    8: 14, // Severity
    9: 45, // Evidence
    10: 70, // AI Explanation
    11: 22, // Reviewer Sign-off
  });
  XLSX.utils.book_append_sheet(workbook, ws2, 'Detailed Exception Log');

  // ==========================================
  // SHEET 3: MATHEMATICAL CHECKS & PRIOR YEAR
  // ==========================================
  const s3Rows: any[][] = [];
  s3Rows.push(['4. MATHEMATICAL REVIEW CHECKS (DETERMINISTIC ENGINE)']);
  s3Rows.push(['Check ID', 'Statement', 'Check Description', 'Formula / Rule', 'Reported Result', 'Calculated Result', 'Variance', 'Status']);
  wp.math_checks.forEach((mc) => {
    s3Rows.push([mc.check_id, mc.statement, mc.check_description, mc.formula_rule, mc.reported_result, mc.calculated_result, mc.variance, mc.status.toUpperCase()]);
  });
  s3Rows.push([]);

  s3Rows.push(['5. PRIOR-YEAR REVIEW (YOY DELTA THRESHOLD ANALYSIS)']);
  s3Rows.push(['Statement', 'Line Item', 'Current-Year Value', 'Prior-Year Value', 'Absolute Change', 'Percentage Change', 'Review Threshold', 'Flagged?', 'Reason for Flag', 'Source Reference']);
  wp.prior_year_checks.forEach((py) => {
    s3Rows.push([
      py.statement,
      py.line_item,
      py.current_year_value,
      py.prior_year_value,
      py.absolute_change,
      `${py.percentage_change}%`,
      py.review_threshold,
      py.flag ? 'FLAGGED' : 'PASS',
      py.reason_for_flag,
      py.source_reference,
    ]);
  });

  const ws3 = XLSX.utils.aoa_to_sheet(s3Rows);
  applyAutoColumnWidths(ws3, s3Rows, {
    0: 16,
    1: 22,
    2: 38,
    3: 30,
    4: 18,
    5: 18,
    6: 16,
    7: 14,
    8: 45,
    9: 28,
  });
  XLSX.utils.book_append_sheet(workbook, ws3, 'Math & Prior-Year Checks');

  // ==========================================
  // SHEET 4: BANKING ANALYTICS & FIELD MAPPINGS
  // ==========================================
  const s4Rows: any[][] = [];
  s4Rows.push(['6. BANKING ANALYTICS & RATIO CHECKS']);
  s4Rows.push(['Metric', 'Current Year', 'Prior Year', 'Movement Change', 'Review Threshold', 'Status', 'Audit Explanation']);
  wp.banking_analytics.forEach((ba) => {
    s4Rows.push([ba.metric, ba.current_year, ba.prior_year, ba.change, ba.threshold, ba.status, ba.explanation]);
  });
  s4Rows.push([]);

  s4Rows.push(['7. WP-514 FIELD MAPPING AUDIT TRAIL']);
  s4Rows.push(['WP 514 Target Field', 'Source Statement', 'Source Line Item', 'Extracted Value', 'Validation Rule Result', 'Exception ID']);
  wp.field_mappings.forEach((fm) => {
    s4Rows.push([fm.wp514_field, fm.source_statement, fm.source_line_item, fm.extracted_value, fm.validation, fm.exception_id]);
  });

  const ws4 = XLSX.utils.aoa_to_sheet(s4Rows);
  applyAutoColumnWidths(ws4, s4Rows, {
    0: 32,
    1: 18,
    2: 24,
    3: 20,
    4: 20,
    5: 16,
    6: 55,
  });
  XLSX.utils.book_append_sheet(workbook, ws4, 'Analytics & Field Mappings');

  // ==========================================
  // SHEET 5: MASTER WP-514 ALL SECTIONS COMBINED
  // ==========================================
  const masterRows: any[][] = [];
  masterRows.push(['WP-514 — FINANCIAL STATEMENT REVIEW WORKING PAPER (FULL MASTER LOG)']);
  masterRows.push([]);

  // 1
  masterRows.push(['1. ENGAGEMENT / REVIEW DETAILS']);
  masterRows.push(['WP Reference', 'WP-514 (2026)']);
  masterRows.push(['Bank Name', wp.engagement_details.bank_name]);
  masterRows.push(['Bank ID', wp.engagement_details.bank_id]);
  masterRows.push(['Reporting Period', wp.engagement_details.reporting_period]);
  masterRows.push(['Comparative Period', wp.engagement_details.comparative_period]);
  masterRows.push(['Currency', wp.engagement_details.currency]);
  masterRows.push(['Reporting Unit', wp.engagement_details.unit]);
  masterRows.push(['Source Document', wp.engagement_details.source_document_current]);
  masterRows.push(['Review Date', wp.engagement_details.review_date]);
  masterRows.push(['Prepared By', wp.engagement_details.prepared_by]);
  masterRows.push(['Reviewed By', wp.engagement_details.reviewed_by]);
  masterRows.push(['Overall Status', wp.engagement_details.overall_status]);
  masterRows.push([]);

  // 2
  masterRows.push(['2. FINANCIAL STATEMENT REVIEW SUMMARY']);
  masterRows.push(['Statement Area', 'Checks Performed', 'Passed', 'Failed', 'Warnings', 'Overall Status']);
  wp.financial_statement_summary.forEach((s) => {
    masterRows.push([s.statement, s.checks_performed, s.passed, s.failed, s.warnings, s.overall_status]);
  });
  masterRows.push([]);

  // 3
  masterRows.push(['3. DETAILED REVIEW FINDINGS / EXCEPTION LOG']);
  masterRows.push([
    'Issue ID',
    'Statement Area',
    'Module Engine',
    'Review Check',
    'Check Status',
    'Reported / Actual',
    'Expected Value',
    'Numeric Variance',
    'Severity',
    'Evidence Reference / Pointers',
    'AI Candidate Narrative Explanation',
    'Reviewer Sign-off Status',
  ]);
  data.findings.forEach((f) => {
    masterRows.push([
      f.finding_id,
      f.statement,
      f.module,
      f.check,
      f.status.toUpperCase(),
      typeof f.actual === 'number' ? `₹${f.actual} Cr` : String(f.actual ?? '—'),
      typeof f.expected === 'number' ? `₹${f.expected} Cr` : String(f.expected ?? '—'),
      f.difference !== null && f.difference !== undefined ? (typeof f.difference === 'number' ? `₹${f.difference} Cr` : String(f.difference)) : '—',
      f.severity.toUpperCase(),
      f.evidence ? f.evidence.map((e) => `${e.table} P.${e.page}`).join('; ') : 'N/A',
      f.ai_explanation ? f.ai_explanation.text || f.ai_explanation.suggested_revision || '' : 'N/A',
      f.reviewer_status,
    ]);
  });
  masterRows.push([]);

  // 4
  masterRows.push(['4. MATHEMATICAL REVIEW CHECKS (DETERMINISTIC ENGINE)']);
  masterRows.push(['Check ID', 'Statement', 'Check Description', 'Formula / Rule', 'Reported Result', 'Calculated Result', 'Variance', 'Status']);
  wp.math_checks.forEach((mc) => {
    masterRows.push([mc.check_id, mc.statement, mc.check_description, mc.formula_rule, mc.reported_result, mc.calculated_result, mc.variance, mc.status.toUpperCase()]);
  });
  masterRows.push([]);

  // 5
  masterRows.push(['5. PRIOR-YEAR REVIEW (YOY DELTA THRESHOLD ANALYSIS)']);
  masterRows.push(['Statement', 'Line Item', 'Current-Year Value', 'Prior-Year Value', 'Absolute Change', 'Percentage Change', 'Review Threshold', 'Flagged?', 'Reason for Flag', 'Source Reference']);
  wp.prior_year_checks.forEach((py) => {
    masterRows.push([
      py.statement,
      py.line_item,
      py.current_year_value,
      py.prior_year_value,
      py.absolute_change,
      `${py.percentage_change}%`,
      py.review_threshold,
      py.flag ? 'FLAGGED' : 'PASS',
      py.reason_for_flag,
      py.source_reference,
    ]);
  });
  masterRows.push([]);

  // 6
  masterRows.push(['6. BANKING ANALYTICS & RATIO CHECKS']);
  masterRows.push(['Metric', 'Current Year', 'Prior Year', 'Movement Change', 'Review Threshold', 'Status', 'Audit Explanation']);
  wp.banking_analytics.forEach((ba) => {
    masterRows.push([ba.metric, ba.current_year, ba.prior_year, ba.change, ba.threshold, ba.status, ba.explanation]);
  });
  masterRows.push([]);

  // 7
  masterRows.push(['7. WP-514 FIELD MAPPING AUDIT TRAIL']);
  masterRows.push(['WP 514 Target Field', 'Source Statement', 'Source Line Item', 'Extracted Value', 'Validation Rule Result', 'Exception ID']);
  wp.field_mappings.forEach((fm) => {
    masterRows.push([fm.wp514_field, fm.source_statement, fm.source_line_item, fm.extracted_value, fm.validation, fm.exception_id]);
  });
  masterRows.push([]);

  // 8
  masterRows.push(['8. OVERALL CONCLUSION & AUDITOR SIGN-OFF']);
  masterRows.push(['Overall Review Result', wp.overall_conclusion.overall_review_result]);
  masterRows.push(['Total Exceptions', wp.overall_conclusion.total_exceptions]);
  masterRows.push(['Critical Exceptions', wp.overall_conclusion.critical_exceptions]);
  masterRows.push(['High Exceptions', wp.overall_conclusion.high_exceptions]);
  masterRows.push(['Medium Exceptions', wp.overall_conclusion.medium_exceptions]);
  masterRows.push(['Key Issues Requiring Attention', wp.overall_conclusion.key_issues_requiring_attention.join('; ')]);
  masterRows.push(['AI-Generated Review Summary', wp.overall_conclusion.ai_generated_review_summary]);
  masterRows.push(['Final Reviewer Decision', finalDecision || wp.overall_conclusion.final_reviewer_decision]);
  masterRows.push(['Reviewer Comments', finalComments || wp.overall_conclusion.reviewer_comments]);

  const wsMaster = XLSX.utils.aoa_to_sheet(masterRows);
  applyAutoColumnWidths(wsMaster, masterRows, {
    0: 25,
    1: 28,
    2: 25,
    3: 32,
    4: 16,
    5: 18,
    6: 18,
    7: 18,
    8: 16,
    9: 35,
    10: 60,
    11: 20,
  });
  XLSX.utils.book_append_sheet(workbook, wsMaster, 'WP-514 Master Working Paper');

  // Trigger download
  const filename = `WP514_${wp.engagement_details.bank_id}_${wp.engagement_details.reporting_period}.xlsx`;
  XLSX.writeFile(workbook, filename);
}
