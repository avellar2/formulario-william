import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  loading?: boolean
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, error, loading, className, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-gray-700">
          {label}
          {props.required && <span className="text-orange-500 ml-1">*</span>}
        </label>
        <div className="relative">
          <input
            ref={ref}
            className={`
              w-full h-12 px-4 rounded-lg border transition-all duration-200 text-gray-900
              bg-white outline-none text-sm placeholder:text-gray-400
              ${error
                ? 'border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-50'
                : 'border-gray-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-50 hover:border-gray-300'
              }
              ${loading ? 'pr-12' : ''}
              ${className ?? ''}
            `}
            {...props}
          />
          {loading && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <div className="w-4 h-4 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        {error && (
          <span className="text-xs text-red-600 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </span>
        )}
      </div>
    )
  }
)

FormField.displayName = 'FormField'
