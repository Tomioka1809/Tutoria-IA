// app/(tutor)/explore.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { Image } from 'expo-image';
import { ExternalLink } from '@/components/external-link';
import ParallaxScrollView from '@/components/parallax-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useExplore } from '@/src/components/explore/useExplore';
import { ExploreHeader } from '@/src/components/explore/ExploreHeader';
import { CollapsibleSection } from '@/src/components/explore/CollapsibleSection';
import { useTranslation } from 'react-i18next';

export default function TabTwoScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const { styles, Fonts, Platform } = useExplore();

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#D0D0D0', dark: '#353636' }}
      headerImage={
        <ExploreHeader style={styles.headerImage} />
      }>
      <ThemedView style={styles.titleContainer}>
        <ThemedText
          type="title"
          style={{
            fontFamily: Fonts.rounded,
          }}>
          {t('explore.title')}
        </ThemedText>
      </ThemedView>
      <ThemedText>{t('explore.intro')}</ThemedText>
      
      <CollapsibleSection title={t('explore.routing')}>
        <ThemedText>
          {t('explore.screens')}{' '}
          <ThemedText type="defaultSemiBold">app/(tutor)/index.tsx</ThemedText> {t('explore.and')}{' '}
          <ThemedText type="defaultSemiBold">app/(tutor)/explore.tsx</ThemedText>
        </ThemedText>
        <ThemedText>
          <ThemedText type="defaultSemiBold">app/(tutor)/_layout.tsx</ThemedText>{' '}
          {t('explore.layout')}
        </ThemedText>
        <ExternalLink href="https://docs.expo.dev/router/introduction">
          <ThemedText type="link">{t('explore.learnMore')}</ThemedText>
        </ExternalLink>
      </CollapsibleSection>

      <CollapsibleSection title={t('explore.platforms')}>
        <ThemedText>{t('explore.platformsBody')}</ThemedText>
      </CollapsibleSection>

      <CollapsibleSection title={t('explore.images')}>
        <ThemedText>{t('explore.imagesBody')}</ThemedText>
        <Image
          source={require('@/assets/images/react-logo.png')}
          style={{ width: 100, height: 100, alignSelf: 'center' }}
        />
        <ExternalLink href="https://reactnative.dev/docs/images">
          <ThemedText type="link">{t('explore.learnMore')}</ThemedText>
        </ExternalLink>
      </CollapsibleSection>

      <CollapsibleSection title={t('explore.themes')}>
        <ThemedText>{t('explore.themesBody')}</ThemedText>
        <ExternalLink href="https://docs.expo.dev/develop/user-interface/color-themes/">
          <ThemedText type="link">{t('explore.learnMore')}</ThemedText>
        </ExternalLink>
      </CollapsibleSection>

      <CollapsibleSection title={t('explore.animations')}>
        <ThemedText>{t('explore.animationsBody')}</ThemedText>
        {Platform.select({
          ios: (
            <ThemedText>
              {t('explore.parallax')}
            </ThemedText>
          ),
        })}
      </CollapsibleSection>
    </ParallaxScrollView>
  );
}
