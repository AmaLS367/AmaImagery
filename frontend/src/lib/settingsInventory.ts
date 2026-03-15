import type { Settings } from './settings'

export type LocalSettingsSectionId =
  | 'appearance'
  | 'mode'
  | 'queue'
  | 'notifications'
  | 'safety'
  | 'presets'

export type LocalSettingsSection = {
  id: LocalSettingsSectionId
  titleKey: string
  descriptionKey: string
}

export const localSettingsSections: LocalSettingsSection[] = [
  {
    id: 'appearance',
    titleKey: 'settings:sections.appearance.title',
    descriptionKey: 'settings:sections.appearance.description',
  },
  {
    id: 'mode',
    titleKey: 'settings:sections.mode.title',
    descriptionKey: 'settings:sections.mode.description',
  },
  {
    id: 'queue',
    titleKey: 'settings:sections.queue.title',
    descriptionKey: 'settings:sections.queue.description',
  },
  {
    id: 'notifications',
    titleKey: 'settings:sections.notifications.title',
    descriptionKey: 'settings:sections.notifications.description',
  },
  {
    id: 'safety',
    titleKey: 'settings:sections.safety.title',
    descriptionKey: 'settings:sections.safety.description',
  },
  {
    id: 'presets',
    titleKey: 'settings:sections.presets.title',
    descriptionKey: 'settings:sections.presets.description',
  },
]

export function findDefaultPreset(settings: Settings) {
  return (
    settings.presets.find((preset) => preset.id === settings.defaultPresetId) ??
    settings.presets[0] ??
    null
  )
}
