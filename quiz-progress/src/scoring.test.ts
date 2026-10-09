import { describe, expect, it } from 'vitest'
import {
  BRACKETS,
  TARGET_POINTS,
  buildPathOptions,
  calculatePlanSummary,
  calculateScenarioNeeds,
  completedQuizzes,
  INITIAL_TOTAL,
  initialFutureQuizzes,
  getPointsForPercentage,
  type QuizResult,
} from './scoring'

describe('DS3500 scoring rules', () => {
  it('maps every percentage boundary to the correct point bracket', () => {
    const cases = [
      [100, 1450],
      [91, 1450],
      [90, 1100],
      [80, 1100],
      [79, 800],
      [61, 800],
      [60, 540],
      [45, 540],
      [44, 200],
      [25, 200],
      [24, 50],
      [1, 50],
      [0, 0],
    ] as const

    for (const [percentage, points] of cases) {
      expect(getPointsForPercentage(percentage)).toBe(points)
    }
  })

  it('uses actual math for quizzes needed by scenario', () => {
    const regularQuizzesRemaining = initialFutureQuizzes.filter((quiz) => !quiz.optional).length
    const scenarios = calculateScenarioNeeds(INITIAL_TOTAL, regularQuizzesRemaining)
    expect(regularQuizzesRemaining).toBe(6)
    expect(scenarios.find((scenario) => scenario.pointsPerQuiz === 1450)?.quizzesNeeded).toBe(2)
    expect(scenarios.find((scenario) => scenario.pointsPerQuiz === 1100)?.quizzesNeeded).toBe(2)
    expect(scenarios.find((scenario) => scenario.pointsPerQuiz === 800)?.quizzesNeeded).toBe(3)
    expect(scenarios.find((scenario) => scenario.pointsPerQuiz === 540)?.quizzesNeeded).toBe(4)
    expect(scenarios.find((scenario) => scenario.pointsPerQuiz === 200)?.achievable).toBe(false)
  })

  it('records Quiz 4 as a completed 85% result and updates the baseline', () => {
    expect(completedQuizzes).toHaveLength(4)
    expect(completedQuizzes[3]).toMatchObject({
      id: 4,
      name: 'Quiz 4',
      percentage: 85,
      points: 1100,
      completed: true,
    })
    expect(INITIAL_TOTAL).toBe(3280)
    expect(initialFutureQuizzes).toHaveLength(7)
    expect(initialFutureQuizzes[0].name).toBe('Quiz 5')
    expect(initialFutureQuizzes.at(-2)?.name).toBe('Quiz 10')
    expect(initialFutureQuizzes.at(-1)).toMatchObject({ name: 'Optional Quiz', optional: true })
  })

  it('uses the optional quiz only to replace the lowest regular score', () => {
    const optionalQuiz = {
      id: 11,
      name: 'Optional Quiz',
      percentage: 85,
      points: 1100,
      completed: false,
      optional: true,
    } as unknown as QuizResult

    const summary = calculatePlanSummary([...completedQuizzes, optionalQuiz])

    expect(summary.total).toBe(3840)
    expect(summary.optionalReplacementGain).toBe(560)
    expect(summary.replacedQuiz?.name).toBe('Quiz 1')
  })

  it('does not lower the total when the optional quiz is below the lowest regular score', () => {
    const optionalQuiz = {
      id: 11,
      name: 'Optional Quiz',
      percentage: 25,
      points: 200,
      completed: false,
      optional: true,
    } as unknown as QuizResult

    const summary = calculatePlanSummary([...completedQuizzes, optionalQuiz])

    expect(summary.total).toBe(3280)
    expect(summary.optionalReplacementGain).toBe(0)
    expect(summary.replacedQuiz).toBeNull()
  })

  it('summarizes mixed future plans without capping totals at the target', () => {
    const summary = calculatePlanSummary([
      ...completedQuizzes,
      { id: 5, name: 'Quiz 5', percentage: 100, points: 1450, completed: false },
      { id: 6, name: 'Quiz 6', percentage: 100, points: 1450, completed: false },
      { id: 7, name: 'Quiz 7', percentage: 100, points: 1450, completed: false },
    ])

    expect(summary.total).toBe(7630)
    expect(summary.reached).toBe(true)
    expect(summary.remaining).toBe(0)
    expect(summary.spare).toBe(2230)
    expect(TARGET_POINTS).toBe(5400)
  })

  it('builds exact bracket-based path options for remaining opportunities', () => {
    const paths = buildPathOptions(2120, 6)
    const mostly80 = paths.find((path) => path.id === 'mostly-80')
    const mixed = paths.find((path) => path.id === 'mixed-80-61')
    const recovery = paths.find((path) => path.id === 'recovery')

    expect(mostly80?.points).toBe(2200)
    expect(mostly80?.achievable).toBe(true)
    expect(mixed?.points).toBe(2440)
    expect(mixed?.achievable).toBe(true)
    expect(recovery?.scores.map((score) => score.points)).toEqual([540, 1100, 1100])
  })

  it('keeps scoring brackets as a simple editable data structure', () => {
    expect(BRACKETS.map((bracket) => bracket.points)).toEqual([1450, 1100, 800, 540, 200, 50, 0])
  })
})
