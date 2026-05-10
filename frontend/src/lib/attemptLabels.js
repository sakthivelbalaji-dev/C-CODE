/** Saved in attempt.feedback when the clock runs out with no code to submit. */
export const TIME_EXPIRED_NO_SUBMISSION_FEEDBACK_PREFIX =
  'Time expired — no graded submission received.'

export function getAttemptOutcomePresentation(isCorrect, feedback) {
  if (isCorrect) {
    return { label: 'Correct', variant: 'success' }
  }
  if (feedback && feedback.includes(TIME_EXPIRED_NO_SUBMISSION_FEEDBACK_PREFIX)) {
    return { label: 'Failed — timed out (reattempt OK)', variant: 'timeout' }
  }
  return { label: 'Wrong', variant: 'failure' }
}

export function getAttemptOutcomeLabel(isCorrect, feedback) {
  return getAttemptOutcomePresentation(isCorrect, feedback).label
}
