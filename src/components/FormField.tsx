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
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <div className="relative">
          <input
            ref={ref}
            className={`
              w-full px-4 py-3 rounded-xl border transition-all duration-200 text-gray-800
              bg-white outline-none text-sm
              ${error
                ? 'border-red-400 focus:border-red-500 focus:ring-2 focus:ring-red-100'
                : 'border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100'
              }
              ${loading ? 'pr-10' : ''}
              ${className ?? ''}
            `}
            {...props}
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        {error && (
          <span className="text-xs text-red-500 flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
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
