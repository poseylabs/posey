
import { UIConfig, UITheme } from '../types/ui';

export const defaultTheme = 'forest';

export const themes: UITheme[] = [
  {label: 'Light', value: 'light'},
  {label: 'Dark', value: 'dark'},
  {label: 'Cupcake', value: 'cupcake'},
  {label: 'Bumblebee', value: 'bumblebee'},
  {label: 'Emerald', value: 'emerald'},
  {label: 'Corporate', value: 'corporate'},
  {label: 'Synthwave', value: 'synthwave'},
  {label: 'Retro', value: 'retro'},
  {label: 'Cyberpunk', value: 'cyberpunk'},
  {label: 'Valentine', value: 'valentine'},
  {label: 'Halloween', value: 'halloween'},
  {label: 'Garden', value: 'garden'},
  {label: 'Forest', value: 'forest'},
  {label: 'Aqua', value: 'aqua'},
  {label: 'Lofi', value: 'lofi'},
  {label: 'Pastel', value: 'pastel'},
  {label: 'Fantasy', value: 'fantasy'},
  {label: 'Wireframe', value: 'wireframe'},
  {label: 'Black', value: 'black'},
  {label: 'Luxury', value: 'luxury'},
  {label: 'Dracula', value: 'dracula'},
  {label: 'Cmyk', value: 'cmyk'},
  {label: 'Autumn', value: 'autumn'},
  {label: 'Business', value: 'business'},
  {label: 'Acid', value: 'acid'},
  {label: 'Lemonade', value: 'lemonade'},
  {label: 'Night', value: 'night'},
  {label: 'Coffee', value: 'coffee'},
  {label: 'Winter', value: 'winter'},
  {label: 'Dim', value: 'dim'},
  {label: 'Nord', value: 'nord'},
  {label: 'Sunset', value: 'sunset'},
]

export const UI_CONFIG: UIConfig = {
  default: defaultTheme,
  themes,
}
