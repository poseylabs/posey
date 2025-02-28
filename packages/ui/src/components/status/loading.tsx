export function Loading({ size = 'lg', variant = 'infinity' }: {size?: 'sm' | 'md' | 'lg', variant?: string }) {
  return <span className={`loading loading-${variant} loading-${size}`} />;
}
