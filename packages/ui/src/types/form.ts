import { ReactNode } from 'react'

export interface IconButtonProps extends Omit<any, 'size' | 'color' | 'variant'> {
  icon?: ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'small' | 'medium' | 'icon'
  'aria-label'?: string
}

export type SelectOption = {
  label: string,
  value: string,
  key?: string
}

export interface SelectProps {
  ariaLabel?: string
  className?: string
  label: string
  key?: string
  options: SelectOption[]
  value?: string
  onChange?: (value: string) => void
}

export interface SwitchProps {
  label: string
  checked?: boolean
  onChange?: (checked: boolean) => void
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary'
}
