'use client';

import React, { useState, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PersonalInfo } from '@/components/dashboard/resume-component';
import { useTranslations } from '@/lib/i18n';
import { Upload, X } from 'lucide-react';

interface PersonalInfoFormProps {
  data: PersonalInfo;
  onChange: (data: PersonalInfo) => void;
}

export const PersonalInfoForm: React.FC<PersonalInfoFormProps> = ({ data, onChange }) => {
  const { t } = useTranslations();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(data.avatar || null);

  const handleChange = (field: keyof PersonalInfo, value: string) => {
    onChange({
      ...data,
      [field]: value,
    });
  };

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        setAvatarPreview(base64);
        handleChange('avatar', base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveAvatar = () => {
    setAvatarPreview(null);
    handleChange('avatar', '');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4 border border-black p-6 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
      <h3 className="font-serif text-xl font-bold border-b border-black pb-2 mb-4">
        {t('builder.personalInfo')}
      </h3>
      
      <div className="mb-6">
        <Label className="font-mono text-xs uppercase tracking-wider text-gray-500 mb-2 block">
          {t('resume.personalInfo.avatar')}
        </Label>
        <div className="flex items-start gap-4">
          {avatarPreview ? (
            <div className="relative">
              <img
                src={avatarPreview}
                alt="Avatar"
                className="w-24 h-24 object-cover border-2 border-black"
              />
              <button
                type="button"
                onClick={handleRemoveAvatar}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-24 h-24 border-2 border-dashed border-black flex flex-col items-center justify-center hover:bg-gray-50 transition-colors"
            >
              <Upload size={24} className="text-gray-400" />
              <span className="text-xs text-gray-500 mt-1">{t('builder.upload')}</span>
            </button>
          )}
          <div className="flex-1">
            <p className="text-sm text-gray-600 mb-2">
              {t('builder.personalInfoForm.avatarHint')}
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              className="hidden"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label
            htmlFor="name"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.name')}
          </Label>
          <Input
            id="name"
            value={data.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.name')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="title"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.title')}
          </Label>
          <Input
            id="title"
            value={data.title || ''}
            onChange={(e) => handleChange('title', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.title')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="email"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.email')}
          </Label>
          <Input
            id="email"
            type="email"
            value={data.email || ''}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.email')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="phone"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.phone')}
          </Label>
          <Input
            id="phone"
            type="tel"
            value={data.phone || ''}
            onChange={(e) => handleChange('phone', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.phone')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="location"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.location')}
          </Label>
          <Input
            id="location"
            value={data.location || ''}
            onChange={(e) => handleChange('location', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.location')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="gender"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.gender')}
          </Label>
          <Input
            id="gender"
            value={data.gender || ''}
            onChange={(e) => handleChange('gender', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.gender')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="age"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.age')}
          </Label>
          <Input
            id="age"
            value={data.age || ''}
            onChange={(e) => handleChange('age', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.age')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="website"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.website')}
          </Label>
          <Input
            id="website"
            value={data.website || ''}
            onChange={(e) => handleChange('website', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.website')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="linkedin"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.linkedin')}
          </Label>
          <Input
            id="linkedin"
            value={data.linkedin || ''}
            onChange={(e) => handleChange('linkedin', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.linkedin')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
        <div className="space-y-2">
          <Label
            htmlFor="github"
            className="font-mono text-xs uppercase tracking-wider text-gray-500"
          >
            {t('resume.personalInfo.github')}
          </Label>
          <Input
            id="github"
            value={data.github || ''}
            onChange={(e) => handleChange('github', e.target.value)}
            placeholder={t('builder.personalInfoForm.placeholders.github')}
            className="rounded-none border-black focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-blue-700 bg-transparent"
          />
        </div>
      </div>
    </div>
  );
};
