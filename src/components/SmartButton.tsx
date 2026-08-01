import React from 'react';

/**
 * A multi-purpose button component that supports various sizes, variants, and states like loading.
 */

type ButtonSize = 'sm' | 'md' | 'lg';
type ButtonVariant = 'primary' | 'secondary' | 'outline';

interface SmartButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-all duration-200',
  secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-4 focus:ring-gray-300 transition-all duration-200',
  outline: 'border border-gray-300 bg-transparent hover:bg-gray-50 focus:ring-4 focus:ring-gray-200 transition-all duration-200',
};

const SmartButton: React.FC<SmartButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading,
  icon,
  className = '',
  disabled,
  children,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all';

  const combinedStyles = `
    ${baseClasses}
    ${variantStyles[variant]}
    ${sizeStyles[size]}
    ${className.trim()}
  `.replace(/\s\s+/g, ' ').trim();

  return (
    <button
      className={combinedStyles}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && (
        <span className="mr-2 h-4 w-4 animate-spin inline-block" aria-hidden="true">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path d="M12 2v20M2 12h20" />
            <path d="M12 8l4 4m-4-4l-4 4" />
          </svg>
        </span>
      )}
      {icon && !isLoading && <span className="mr-2">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};

export default SmartButton;
