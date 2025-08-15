import * as React from 'react'
import * as SelectPrimitive from '@radix-ui/react-select'
import { ChevronDown, ChevronUp, Check } from 'lucide-react'

interface Option { value: string; label: string }
interface Props {
  value?: string
  onChange?: (v: string) => void
  options: Option[]
  placeholder?: string
  clearable?: boolean
}

export const Select: React.FC<Props> = ({ value, onChange, options, placeholder, clearable = true }) => {
  const [open, setOpen] = React.useState(false)
  const handleValueChange = (next: string) => {
    // Si même valeur et clearable, on vide
    if (clearable && next === (value || '')) {
      onChange && onChange('')
      setOpen(false)
      return
    }
    onChange && onChange(next)
  }

  return (
    // Radix Select interdit les Item avec value="". On utilise undefined pour l'état "aucun" et on n'affiche pas l'item vide.
    <SelectPrimitive.Root open={open} onOpenChange={setOpen} value={value || undefined} onValueChange={handleValueChange}>
      <SelectPrimitive.Trigger
        className="inline-flex items-center justify-between rounded-md border px-3 py-1.5 text-sm w-60 bg-white text-gray-900 border-gray-300 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        onKeyDown={(e) => {
          if (clearable && (e.key === 'Backspace' || e.key === 'Delete') && value) {
            e.preventDefault()
            onChange && onChange('')
          }
        }}
      >
        <SelectPrimitive.Value placeholder={placeholder || 'Sélectionner...'} />
        <SelectPrimitive.Icon>
          <ChevronDown className="h-4 w-4" />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content className="overflow-hidden rounded-md border bg-white text-gray-900 shadow-lg border-gray-200">
          <SelectPrimitive.ScrollUpButton className="flex items-center justify-center p-1">
            <ChevronUp className="h-4 w-4" />
          </SelectPrimitive.ScrollUpButton>
          <SelectPrimitive.Viewport className="p-1 bg-white">
            {options.filter(opt => opt.value !== '').map(opt => (
              <SelectPrimitive.Item
                key={opt.value}
                value={opt.value}
                onSelect={(e) => {
                  if (clearable && value === opt.value) {
                    e.preventDefault()
                    onChange && onChange('')
                    setOpen(false)
                  }
                }}
                className="relative flex cursor-default select-none items-center rounded px-2 py-1.5 text-sm outline-none text-gray-900 hover:bg-gray-100 data-[state=checked]:bg-blue-50 data-[state=checked]:text-blue-700"
              >
                <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>
                <SelectPrimitive.ItemIndicator className="absolute right-2 inline-flex items-center">
                  <Check className="h-4 w-4" />
                </SelectPrimitive.ItemIndicator>
              </SelectPrimitive.Item>
            ))}
          </SelectPrimitive.Viewport>
          <SelectPrimitive.ScrollDownButton className="flex items-center justify-center p-1">
            <ChevronDown className="h-4 w-4" />
          </SelectPrimitive.ScrollDownButton>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  )
}


