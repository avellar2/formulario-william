interface Step {
  label: string
}

interface StepperProps {
  steps: Step[]
  current: number
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div className="flex items-center justify-center">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300
                ${index < current ? 'bg-orange-500 text-white' : ''}
                ${index === current ? 'bg-gray-900 text-white ring-4 ring-gray-100' : ''}
                ${index > current ? 'bg-gray-100 text-gray-400' : ''}
              `}
            >
              {index < current ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`mt-2 text-xs font-medium transition-colors duration-300
                ${index === current ? 'text-gray-900' : index < current ? 'text-orange-600' : 'text-gray-400'}
              `}
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`w-16 sm:w-24 h-px mx-3 mb-6 transition-all duration-300
                ${index < current ? 'bg-orange-500' : 'bg-gray-200'}
              `}
            />
          )}
        </div>
      ))}
    </div>
  )
}
