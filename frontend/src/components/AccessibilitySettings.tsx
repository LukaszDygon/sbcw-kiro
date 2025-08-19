/**
 * Accessibility Settings component
 * Allows users to configure accessibility preferences
 */
import React from 'react'
import { useAccessibility } from '../contexts/AccessibilityContext'

interface AccessibilitySettingsProps {
  isOpen: boolean
  onClose: () => void
}

const AccessibilitySettings: React.FC<AccessibilitySettingsProps> = ({ isOpen, onClose }) => {
  const { preferences, updatePreferences } = useAccessibility()

  if (!isOpen) return null

  const handleThemeChange = (theme: 'default' | 'high-contrast') => {
    updatePreferences({ theme })
  }

  const handleFontSizeChange = (fontSize: 'default' | 'large' | 'extra-large') => {
    updatePreferences({ fontSize })
  }

  const handleMotionToggle = () => {
    updatePreferences({ reduceMotion: !preferences.reduceMotion })
  }

  const handleAnnouncementsToggle = () => {
    updatePreferences({ screenReaderAnnouncements: !preferences.screenReaderAnnouncements })
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="accessibility-settings-title">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          aria-hidden="true"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <h3 
                  className="text-lg leading-6 font-medium text-gray-900 mb-4"
                  id="accessibility-settings-title"
                >
                  Accessibility Settings
                </h3>

                <div className="space-y-6">
                  {/* Theme Selection */}
                  <fieldset>
                    <legend className="text-sm font-medium text-gray-900 mb-3">
                      Display Theme
                    </legend>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="theme"
                          value="default"
                          checked={preferences.theme === 'default'}
                          onChange={() => handleThemeChange('default')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                        />
                        <span className="ml-3 text-sm text-gray-700">Default Theme</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="theme"
                          value="high-contrast"
                          checked={preferences.theme === 'high-contrast'}
                          onChange={() => handleThemeChange('high-contrast')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                        />
                        <span className="ml-3 text-sm text-gray-700">High Contrast Theme</span>
                      </label>
                    </div>
                  </fieldset>

                  {/* Font Size Selection */}
                  <fieldset>
                    <legend className="text-sm font-medium text-gray-900 mb-3">
                      Text Size
                    </legend>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="fontSize"
                          value="default"
                          checked={preferences.fontSize === 'default'}
                          onChange={() => handleFontSizeChange('default')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                        />
                        <span className="ml-3 text-sm text-gray-700">Default Size</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="fontSize"
                          value="large"
                          checked={preferences.fontSize === 'large'}
                          onChange={() => handleFontSizeChange('large')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                        />
                        <span className="ml-3 text-sm text-gray-700">Large Text</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          name="fontSize"
                          value="extra-large"
                          checked={preferences.fontSize === 'extra-large'}
                          onChange={() => handleFontSizeChange('extra-large')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                        />
                        <span className="ml-3 text-sm text-gray-700">Extra Large Text</span>
                      </label>
                    </div>
                  </fieldset>

                  {/* Motion Preferences */}
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.reduceMotion}
                        onChange={handleMotionToggle}
                        className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                      <span className="ml-3 text-sm text-gray-700">
                        Reduce motion and animations
                      </span>
                    </label>
                    <p className="mt-1 text-xs text-gray-500 ml-7">
                      Minimizes animations and transitions for users sensitive to motion
                    </p>
                  </div>

                  {/* Screen Reader Announcements */}
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.screenReaderAnnouncements}
                        onChange={handleAnnouncementsToggle}
                        className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                      <span className="ml-3 text-sm text-gray-700">
                        Enable screen reader announcements
                      </span>
                    </label>
                    <p className="mt-1 text-xs text-gray-500 ml-7">
                      Provides audio feedback for important actions and status changes
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Modal actions */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={onClose}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AccessibilitySettings