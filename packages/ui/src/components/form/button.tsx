import { mergeClasses } from '../../utils/cn';
import { forwardRef } from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  id?: string;
  variant?: 'default' | 'outline' | 'ghost' | 'link';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

interface ButtonRef extends HTMLButtonElement {
  loading: boolean;
}

export const Button = forwardRef<ButtonRef, ButtonProps>(
  ({ 
    className,
    id,
    variant = 'default', 
    size = 'md',
    isLoading,
    disabled,
    children,
    ...props 
  }: ButtonProps, ref) => {
    const baseClasses = 'btn';
    
    const variantClasses = {
      default: 'btn-primary',
      outline: 'btn-outline',
      ghost: 'btn-ghost',
      link: 'btn-link'
    };

    const sizeClasses = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg'
    };

    return (
      <button
        ref={ref}
        id={id}
        className={mergeClasses(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          isLoading && 'loading',
          className
        )}
        disabled={isLoading || disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button'; 
