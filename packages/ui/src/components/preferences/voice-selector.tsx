'use client';

import { usePoseyState } from '@posey.ai/state';
import { config, Voice } from '@posey.ai/core';
import { useEffect, useState } from 'react';

const style = {
  h3: "font-bold ",
  label: "text-sm font-bold mb-2 block mt-4",
}

// const topVoices = [
//   {
//     name: 'Niamh',
//     voice_id: '1e9Gn3OQenGu4rjQ3Du1',
//     language: 'en',
//   },
//   {
//     name: '',
//   }
// ]

export const VoiceSelector = ({ speechAbility }: { speechAbility: any }) => {
  const store = usePoseyState();
  const { user, setUserPreferences } = store.select(state => ({
    user: state.user,
    setUserPreferences: state.setUserPreferences,
  }));

  const { lang } = config;
  const { languages } = lang;

  const [voicesByLanguage, setVoicesByLanguage] = useState<Record<string, Voice[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const preferences = user?.metadata?.preferences;
  const preferredVoices = preferences?.preferred_voices || {};
  const [selectedVoiceId, setSelectedVoiceId] = useState('');

  useEffect(() => {
    if (preferredVoices[preferences?.language]) {
      setSelectedVoiceId(preferredVoices[preferences.language]);
    }
  }, [preferredVoices, preferences?.language]);

  useEffect(() => {
    const fetchVoices = async () => {
      try {
        // Access the speech ability directly through Posey
        if (speechAbility?.getVoices) {
          const voices = await speechAbility.getVoices();

          // Group voices by language
          const grouped = voices.reduce((acc: Record<string, Voice[]>, voice: any) => {
            languages.forEach(lang => {
              if (!acc[lang.code]) acc[lang.code] = [];

              if (voice.language === lang.code || voice?.labels?.language === lang.code) {
                acc[lang.code].push(voice);
              } else if (lang.code === 'en' && !voice?.labels?.language) {
                // console.warn('Adding voice with no language to en', voice);
                acc['en'].push(voice);
              }
            });
            return acc;
          }, {} as Record<string, Voice[]>);

          setVoicesByLanguage(grouped);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error fetching voices:', error);
        setIsLoading(false);
      }
    };

    fetchVoices();
  }, [speechAbility]);

  const handleVoiceChange = (languageCode: string, voiceId: string) => {
    const newPreferredVoices = {
      ...preferredVoices,
      [languageCode]: voiceId
    };

    setUserPreferences({
      preferences: {
        ...preferences,
        preferred_voices: newPreferredVoices,
        language: languageCode
      }
    });
    setSelectedVoiceId(voiceId);
  };

  const parseVoiceUseCase = (useCase: any) => {
    return useCase.split('_').join(', ');
  };

  return (
    <ul className="w-full">
      {languages.map((language: {
        code: string;
        name: string;
        defaultVoiceId: string;
      }) => (
        <li key={language.code}>
          {/* <label className={style.label}>Preferred Voice</label> */}
          <label className={style.label}>{language.name} Voice</label>
          <select
            className="select select-bordered mb-1 w-full max-w-[calc(100%-1rem)] text-ellipsis"
            onChange={(e) => handleVoiceChange(language.code, e.target.value)}
            value={selectedVoiceId}
          >
            {voicesByLanguage[language.code]?.map((voice: any) => (
              <option key={voice.voice_id} value={voice.voice_id}>{voice.name} ({parseVoiceUseCase(voice?.labels?.use_case)})</option>
            ))}
          </select>
        </li>
      ))}
    </ul>
  );
};
