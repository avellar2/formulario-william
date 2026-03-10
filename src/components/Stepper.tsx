interface Step {
  label: string
  icon: string
}

interface StepperProps {
  steps: Step[]
  current: number
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div className="flex items-center justify-center mb-8 px-4">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`
                w-12 h-12 rounded-full flex items-center justify-center text-xl font-semibold transition-all duration-300
                ${index < current ? 'bg-blue-500 text-white shadow-lg shadow-blue-200' : ''}
                ${index === current ? 'bg-blue-600 text-white shadow-lg shadow-blue-300 scale-110' : ''}
                ${index > current ? 'bg-white text-gray-400 border-2 border-gray-200' : ''}
              `}
            >
              {index < current ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span>{step.icon}</span>
              )}
            </div>
            <span
              className={`mt-2 text-xs font-medium transition-colors duration-300 text-center max-w-16
                ${index === current ? 'text-blue-600' : index < current ? 'text-blue-400' : 'text-gray-400'}
              `}
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`w-16 sm:w-24 h-0.5 mx-2 mb-5 transition-all duration-500
                ${index < current ? 'bg-blue-400' : 'bg-gray-200'}
              `}
            />
          )}
        </div>
      ))}
    </div>
  )
}
