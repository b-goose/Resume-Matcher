'use client';

import React, { useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useTranslations } from '@/lib/i18n';

interface GenericListFormProps {
  items: string[];
  onChange: (items: string[]) => void;
  label?: string;
  placeholder?: string;
}

/**
 * Generic List Form Component
 *
 * Used for STRING_LIST type sections (like Skills).
 * Renders a textarea where items are separated by newlines.
 */
export const GenericListForm: React.FC<GenericListFormProps> = ({
  items,
  onChange,
  label,
  placeholder,
}) => {
  const { t } = useTranslations();
  const finalLabel = label ?? t('builder.customSections.itemsLabel');
  const finalPlaceholder = placeholder ?? t('builder.customSections.itemsPlaceholder');

  const handleChange = useCallback((value: string) => {
    onChange(value.split('\n'));
  }, [onChange]);

  const textValue = items?.join('\n') || '';

  return (
    <div className="space-y-2">
      <Label className="font-mono text-xs uppercase tracking-wider text-gray-500">
        {finalLabel}
      </Label>
      <p className="font-mono text-xs text-blue-700 border-l-2 border-blue-700 pl-3 mb-2">
        {t('builder.additionalForm.instructions')}
      </p>
      <Textarea
        value={textValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={finalPlaceholder}
        className="min-h-[150px] text-black rounded-none border-black bg-white focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700"
      />
    </div>
  );
};
