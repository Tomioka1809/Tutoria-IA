// src/components/explore/CollapsibleSection.tsx
import React from 'react';
import { Collapsible } from '@/components/ui/collapsible';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
}

export function CollapsibleSection({ title, children }: CollapsibleSectionProps) {
  return (
    <Collapsible title={title}>
      {children}
    </Collapsible>
  );
}
