// Display text for the API's recommendation values.
// The screen never invents wording; it only translates the API's value.
export const RECOMMENDATION_LABEL = {
  ALLOW: 'Continue with normal care',
  REVIEW: 'Pause and confirm',
  VERIFY: 'Verify before sending',
  STOP_AND_VERIFY: 'Stop and verify',
}

export const levelClass = (level) => `lvl-${level.toLowerCase()}`

export const levelLabel = (level) =>
  level.charAt(0) + level.slice(1).toLowerCase()