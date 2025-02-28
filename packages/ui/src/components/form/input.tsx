import { forwardRef, useState } from 'react';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onSubmit'> {
  error?: string;
  className?: string;
  defaultValue?: string;
  id?: string;
  label?: string;
  type?: string;
  resetOnSubmit?: boolean;
  placeholder?: string;
  value?: string;
  validate?: (value: string) => Promise<string | undefined>;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, id, label, type, placeholder, validate, ...props }, ref) => {
    const [validationError, setValidationError] = useState<string | undefined>(undefined);

    const handleValidation = async (value: string) => {
      if (validate) {
        const result = await validate(value);
        setValidationError(result);
      }
    };

    return (
      <div className="form-control w-full">
        {label && <label htmlFor={id} className="label">
          <span className="label-text">{label}</span>
        </label>}
        <input
          ref={ref}
          id={id}
          type={type}
          placeholder={placeholder}
          className={className ||  'input input-bordered w-full'}
          {...props}
          onChange={(e) => handleValidation(e.target.value)}
        />
        {error && (
          <label className="label">
            <span className="label-text-alt text-error">{error}</span>
          </label>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
