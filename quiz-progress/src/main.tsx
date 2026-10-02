import { StrictMode, useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Moon, RefreshCcw, Sun, Trophy } from 'lucide-react'
import './styles.css'
import {
  BRACKETS,
  INITIAL_TOTAL,
  TARGET_POINTS,
  buildPathOptions,
  calculatePlanSummary,
  calculateScenarioNeeds,
  completedQuizzes,
  getBracketForPercentage,
  getPointsForPercentage,
  initialFutureQuizzes,
  type QuizResult,
} from './scoring'

const STORAGE_KEY = 'ds3500-quiz-progress:v3'
const THEME_KEY = 'ds3500-quiz-progress:theme'

function formatPoints(points: number) {
  return points.toLocaleString()
}

function loadFutureQuizzes(): QuizResult[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return initialFutureQuizzes
    const parsed = JSON.parse(saved) as QuizResult[]

    return initialFutureQuizzes.map((quiz) => {
      const savedQuiz = parsed.find((item) => item.id === quiz.id)
      return savedQuiz ? { ...quiz, percentage: savedQuiz.percentage, points: savedQuiz.points } : quiz
    })
  } catch {
    return initialFutureQuizzes
  }
}

function App() {
  const [futureQuizzes, setFutureQuizzes] = useState<QuizResult[]>(loadFutureQuizzes)
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) ?? 'light')

  const allQuizzes = useMemo(() => [...completedQuizzes, ...futureQuizzes], [futureQuizzes])
  const summary = useMemo(() => calculatePlanSummary(allQuizzes), [allQuizzes])
  const regularQuizzesRemaining = initialFutureQuizzes.filter((quiz) => !quiz.optional).length
  const baseScenarioNeeds = useMemo(() => calculateScenarioNeeds(INITIAL_TOTAL, regularQuizzesRemaining), [regularQuizzesRemaining])
  const pathOptions = useMemo(() => buildPathOptions(TARGET_POINTS - INITIAL_TOTAL, regularQuizzesRemaining), [regularQuizzesRemaining])
  const progressPercent = Math.min((summary.total / TARGET_POINTS) * 100, 100)
  const rawProgressPercent = (summary.total / TARGET_POINTS) * 100

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(futureQuizzes))
  }, [futureQuizzes])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  function updateQuiz(id: number, percentage: number | null) {
    setFutureQuizzes((quizzes) =>
      quizzes.map((quiz) => {
        if (quiz.id !== id) return quiz
        return {
          ...quiz,
          percentage,
          points: percentage === null ? 0 : getPointsForPercentage(percentage),
        }
      }),
    )
  }

  function reset() {
    setFutureQuizzes(initialFutureQuizzes)
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">DS3500 progress studio</p>
          <h1>DS3500 Quiz Progress Calculator</h1>
        </div>
        <div className="topbar-actions">
          <button className="icon-button" type="button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label="Toggle dark mode">
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
          <button className="secondary-button" type="button" onClick={reset}>
            <RefreshCcw size={16} />
            Reset
          </button>
        </div>
      </header>

      <section className={`hero-panel ${summary.reached ? 'reached' : ''}`}>
        <div className="hero-grid">
          <div>
            <p className="eyebrow">Current total</p>
            <div className="scoreline">{formatPoints(summary.total)} / {formatPoints(TARGET_POINTS)}</div>
            <p className="hero-note">
              {summary.reached ? 'Target Reached! 🎉' : `${formatPoints(summary.remaining)} points remaining`}
            </p>
          </div>
          <div className="target-badge" style={{ '--pct': `${progressPercent}%` } as React.CSSProperties} aria-label={`${rawProgressPercent.toFixed(1)} percent completed`}>
            <span>{rawProgressPercent.toFixed(1)}%</span>
            <small>of target completed</small>
          </div>
        </div>
        <div className="progress-track" aria-label="Progress toward 5400 points">
          <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
        <div className="stat-grid">
          <Metric label="Points remaining" value={formatPoints(summary.remaining)} />
          <Metric label="Quizzes completed" value={String(summary.completedCount)} />
          <Metric label="Future points planned" value={`+${formatPoints(summary.futurePoints)}`} />
          <Metric label="Opportunities remain" value={`${regularQuizzesRemaining} regular + 1 optional`} />
        </div>
        <div className="completed-strip">
          {completedQuizzes.map((quiz) => (
            <span key={quiz.id}>{quiz.name}: {quiz.percentage}% {'->'} +{quiz.points}</span>
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Future quiz simulator</p>
            <h2>Try percentages or pick a bracket</h2>
          </div>
          <p>{summary.message}</p>
        </div>
        <div className="quiz-grid">
          {futureQuizzes.map((quiz) => (
            <article className={`quiz-card ${quiz.optional ? 'optional-quiz' : ''}`} key={quiz.id}>
              <div className="quiz-card-top">
                <h3>{quiz.name}{quiz.optional ? ' · replaces lowest' : ''}</h3>
                <strong>+{formatPoints(quiz.optional ? summary.optionalReplacementGain : quiz.points)}</strong>
              </div>
              <label>
                Percentage
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="0-100"
                  value={quiz.percentage ?? ''}
                  onChange={(event) => {
                    const value = event.currentTarget.value
                    updateQuiz(quiz.id, value === '' ? null : Number(value))
                  }}
                />
              </label>
              <label>
                Bracket
                <select
                  value={quiz.percentage === null ? '' : getBracketForPercentage(quiz.percentage).label}
                  onChange={(event) => {
                    const bracket = BRACKETS.find((item) => item.label === event.currentTarget.value)
                    updateQuiz(quiz.id, bracket ? bracket.min : null)
                  }}
                >
                  <option value="">Choose a bracket</option>
                  {BRACKETS.map((bracket) => (
                    <option key={bracket.label} value={bracket.label}>
                      {bracket.label} {'->'} {bracket.points} pts
                    </option>
                  ))}
                </select>
              </label>
              <p className="bracket-note">
                {quiz.percentage === null
                  ? quiz.optional ? 'Only counts when it improves your lowest regular quiz' : 'No score planned yet'
                  : quiz.optional
                    ? summary.optionalReplacementGain > 0
                      ? `Replaces ${summary.replacedQuiz?.name}: net +${formatPoints(summary.optionalReplacementGain)}`
                      : 'Does not improve the current lowest regular score'
                    : `${getBracketForPercentage(quiz.percentage).label} bracket`}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block split-layout">
        <div className="panel">
          <p className="eyebrow">How many quizzes do I need?</p>
          <h2>Scenario calculator</h2>
          <div className="scenario-list">
            {baseScenarioNeeds.map((scenario) => (
              <div className={`scenario-row ${scenario.achievable ? '' : 'warning'}`} key={scenario.label}>
                <div>
                  <strong>If I average {scenario.label}</strong>
                  <span>{scenario.pointsPerQuiz} points per quiz</span>
                </div>
                <b>{scenario.quizzesNeeded} quiz{scenario.quizzesNeeded === 1 ? '' : 'zes'}</b>
                <small>{scenario.achievable ? 'Fits remaining opportunities' : 'More than available'}</small>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <p className="eyebrow">Plan my path to 5400</p>
          <h2>Mixed score summary</h2>
          <div className="plan-meter">
            <div>
              <span>Projected final points</span>
              <strong>{formatPoints(summary.total)}</strong>
            </div>
            <div>
              <span>Still needed</span>
              <strong>{formatPoints(summary.remaining)}</strong>
            </div>
            <div>
              <span>Additional top-score quizzes</span>
              <strong>{summary.additionalQuizzesNeeded}</strong>
            </div>
            <div>
              <span>Optional replacement gain</span>
              <strong>+{formatPoints(summary.optionalReplacementGain)}</strong>
            </div>
          </div>
          <p className={`callout ${summary.reached ? 'success' : ''}`}>
            {summary.reached ? <Trophy size={18} /> : null}
            {summary.message}
          </p>
        </div>
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <p className="eyebrow">What do I need next?</p>
            <h2>Bracket-based paths that can still work</h2>
          </div>
          <p>Each path uses the exact point brackets and the {regularQuizzesRemaining} remaining regular quizzes. The optional quiz can improve the result further.</p>
        </div>
        <div className="path-grid">
          {pathOptions.map((path) => (
            <article className={`path-card ${path.achievable ? '' : 'warning'}`} key={path.id}>
              <div className="path-card-top">
                <h3>{path.title}</h3>
                <span>{path.achievable ? 'Achievable' : 'Not enough'}</span>
              </div>
              <p>{path.description}</p>
              <div className="score-chips">
                {path.scores.map((item, index) => (
                  <span key={`${path.id}-${index}`}>{item.label}: +{item.points}</span>
                ))}
              </div>
              <strong>{formatPoints(path.points)} planned points</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block reference-band">
        <div>
          <p className="eyebrow">Score bracket reference</p>
          <h2>Conversion table</h2>
        </div>
        <div className="reference-grid">
          {BRACKETS.map((bracket) => (
            <div className="reference-card" key={bracket.label}>
              <span>{bracket.label}</span>
              <strong>{bracket.points} pts</strong>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
