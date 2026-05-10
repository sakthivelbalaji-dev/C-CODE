/** Must match backend `app/email_policy.py` ALLOWED_EMAIL_DOMAIN */

export const ALLOWED_EMAIL_DOMAIN = 'rajalakshmi.edu.in'

export const EMAIL_DOMAIN_REJECT_MESSAGE = `Only ${ALLOWED_EMAIL_DOMAIN} is allowed. Use something like name@${ALLOWED_EMAIL_DOMAIN}.`

export function normalizeInstitutionalEmail(email) {
  return String(email ?? '')
    .trim()
    .toLowerCase()
}

export function isAllowedInstitutionalEmail(email) {
  const normalized = normalizeInstitutionalEmail(email)
  const at = normalized.lastIndexOf('@')
  if (at < 1) return false
  const local = normalized.slice(0, at)
  const domain = normalized.slice(at + 1)
  return local.length > 0 && domain === ALLOWED_EMAIL_DOMAIN
}
