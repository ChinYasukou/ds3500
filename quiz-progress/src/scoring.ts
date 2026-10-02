export const TARGET_POINTS = 5400
export const INITIAL_TOTAL = 2180

export const BRACKETS = [
  { label: '91-100%', min: 91, max: 100, points: 1450 },
  { label: '80-90%', min: 80, max: 90, points: 1100 },
  { label: '61-79%', min: 61, max: 79, points: 800 },
  { label: '45-60%', min: 45, max: 60, points: 540 },
  { label: '25-44%', min: 25, max: 44, points: 200 },
  { label: '1-24%', min: 1, max: 24, points: 50 },
  { label: '0%', min: 0, max: 0, points: 0 },
] as const

export type Bracket = (typeof BRACKETS)[number]

export type QuizResult = {
  id: number
  name: string
  percentage: number | null
  points: number
  completed: boolean
  optional?: boolean
}

export const completedQuizzes: QuizResult[] = [
  { id: 1, name: 'Quiz 1', percentage: 55, points: 540, completed: true },
  { id: 2, name: 'Quiz 2', percentage: 85, points: 1100, completed: true },
  { id: 3, name: 'Quiz 3', percentage: 60, points: 540, completed: true },
]

const futureQuizDefinitions = [
  { id: 4, name: 'Quiz 4' },
  { id: 5, name: 'Quiz 5' },
  { id: 6, name: 'Quiz 6' },
  { id: 7, name: 'Quiz 7' },
  { id: 8, name: 'Quiz 8' },
  { id: 9, name: 'Quiz 9' },
  { id: 10, name: 'Quiz 10' },
  { id: 11, name: 'Optional Quiz', optional: true },
]

export const initialFutureQuizzes: QuizResult[] = futureQuizDefinitions.map((quiz) => ({
  ...quiz,
  percentage: null,
  points: 0,
  completed: false,
}))

export function clampPercentage(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value)))
}

export function getBracketForPercentage(percentage: number): Bracket {
  const safePercentage = clampPercentage(percentage)
  return BRACKETS.find((bracket) => safePercentage >= bracket.min && safePercentage <= bracket.max) ?? BRACKETS.at(-1)!
}

export function getPointsForPercentage(percentage: number): number {
  return getBracketForPercentage(percentage).points
}

export function calculateScenarioNeeds(currentTotal: number, opportunitiesRemaining: number) {
  const pointsRemaining = Math.max(TARGET_POINTS - currentTotal, 0)

  return BRACKETS.filter((bracket) => bracket.points > 0).map((bracket) => {
    const quizzesNeeded = Math.ceil(pointsRemaining / bracket.points)

    return {
      label: bracket.label,
      pointsPerQuiz: bracket.points,
      quizzesNeeded,
      achievable: quizzesNeeded <= opportunitiesRemaining,
    }
  })
}

export function calculatePlanSummary(quizzes: QuizResult[]) {
  const regularQuizzes = quizzes.filter((quiz) => !quiz.optional)
  const optionalQuiz = quizzes.find((quiz) => quiz.optional)
  const scoredRegularQuizzes = regularQuizzes.filter((quiz) => quiz.percentage !== null)
  const lowestRegularQuiz = scoredRegularQuizzes.reduce<QuizResult | null>(
    (lowest, quiz) => (lowest === null || quiz.points < lowest.points ? quiz : lowest),
    null,
  )
  const optionalReplacementGain = optionalQuiz && optionalQuiz.percentage !== null && lowestRegularQuiz
    ? Math.max(optionalQuiz.points - lowestRegularQuiz.points, 0)
    : 0
  const replacedQuiz = optionalReplacementGain > 0 ? lowestRegularQuiz : null
  const regularTotal = regularQuizzes.reduce((sum, quiz) => sum + quiz.points, 0)
  const total = regularTotal + optionalReplacementGain
  const remaining = Math.max(TARGET_POINTS - total, 0)
  const spare = Math.max(total - TARGET_POINTS, 0)
  const futurePoints = regularQuizzes.filter((quiz) => !quiz.completed).reduce((sum, quiz) => sum + quiz.points, 0) + optionalReplacementGain
  const plannedFutureCount = quizzes.filter((quiz) => !quiz.completed && quiz.percentage !== null).length
  const additionalQuizzesNeeded = remaining === 0 ? 0 : Math.ceil(remaining / BRACKETS[0].points)

  let message = `You need ${remaining.toLocaleString()} more points.`
  if (remaining > 0 && remaining <= 540) {
    message = `You are only ${remaining.toLocaleString()} points away.`
  }
  if (spare > 0) {
    message = `You reached the 5400-point requirement with ${spare.toLocaleString()} points to spare.`
  } else if (remaining === 0) {
    message = 'You reached the 5400-point requirement exactly.'
  }

  return {
    total,
    remaining,
    spare,
    reached: total >= TARGET_POINTS,
    completedCount: quizzes.filter((quiz) => quiz.completed).length,
    plannedFutureCount,
    futurePoints,
    additionalQuizzesNeeded,
    optionalReplacementGain,
    replacedQuiz,
    message,
  }
}

function score(label: string, points: number) {
  return { label, points }
}

export function buildPathOptions(pointsRemaining: number, opportunitiesRemaining: number) {
  const paths = [
    {
      id: 'mostly-80',
      title: 'Mostly 80-90%',
      description: 'Three solid 1100-point quizzes reach the requirement.',
      scores: [score('80-90%', 1100), score('80-90%', 1100), score('80-90%', 1100)],
    },
    {
      id: 'mostly-61',
      title: 'Mostly 61-79%',
      description: 'Five 800-point quizzes clears the remaining gap.',
      scores: [score('61-79%', 800), score('61-79%', 800), score('61-79%', 800), score('61-79%', 800), score('61-79%', 800)],
    },
    {
      id: 'mixed-80-61',
      title: 'Blend 80-90% and 61-79%',
      description: 'Three 1100-point quizzes plus one 800-point quiz gives breathing room.',
      scores: [score('80-90%', 1100), score('80-90%', 1100), score('80-90%', 1100), score('61-79%', 800)],
    },
    {
      id: 'recovery',
      title: 'One weaker quiz, then stronger',
      description: 'A 540-point quiz can still fit if the next three land in the 80-90% bracket.',
      scores: [score('45-60%', 540), score('80-90%', 1100), score('80-90%', 1100), score('80-90%', 1100)],
    },
  ]

  return paths.map((path) => {
    const points = path.scores.reduce((sum, item) => sum + item.points, 0)

    return {
      ...path,
      points,
      achievable: points >= pointsRemaining && path.scores.length <= opportunitiesRemaining,
    }
  })
}
