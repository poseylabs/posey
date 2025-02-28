export interface UITheme {
  label: string;
  value: string;
}

export interface UIConfig {
  default: string;
  themes: UITheme[];
}
