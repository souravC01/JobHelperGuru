// Only static styles are interpreted; all document content is inserted as text.
export function renderCoverLetter(document, { candidateName, company, subject, body, dateLabel }) {
  document.head.replaceChildren();
  document.body.replaceChildren();
  document.documentElement.lang = 'en';
  document.title = `Cover Letter - ${candidateName} - ${company}`;
  const style = document.createElement('style');
  style.textContent = `
    @page { margin: 1in; size: letter; }
    body { font-family: Arial, sans-serif; color: #1e293b; margin: 0; padding: 24px; font-size: 11pt; line-height: 1.6; }
    .name { font-size: 16pt; font-weight: bold; margin-bottom: 4px; }
    .date { font-size: 10pt; color: #64748b; margin-bottom: 16px; }
    .recipient, .subject { margin-bottom: 16px; white-space: pre-wrap; }
    .subject { font-weight: bold; }
    p { margin: 0 0 14px; white-space: pre-wrap; overflow-wrap: anywhere; }
    @media print { body { padding: 0; } }
  `;
  document.head.appendChild(style);
  const append = (tag, value, className = '') => {
    const node = document.createElement(tag);
    node.textContent = String(value ?? '');
    node.className = className;
    document.body.appendChild(node);
  };
  append('div', candidateName, 'name');
  append('div', dateLabel, 'date');
  append('div', ['Hiring Team', company].filter(Boolean).join('\n'), 'recipient');
  if (subject) append('div', `Subject: ${subject}`, 'subject');
  String(body ?? '').split(/\r?\n\r?\n/).forEach(paragraph => append('p', paragraph));
}
