import React from "react";
import { motion } from "framer-motion";
import { IMG } from "./utils/images";
import "../styles/prompt-guide.css";
import { useTranslation } from "react-i18next";

type Variant = "good" | "bad";

interface ExampleItem {
  id: string;
  variant: Variant;
  img: string;
  prompt: string;
}

const Pill: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="pg-pill">{children}</span>
);

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = React.useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1000);
    } catch {}
  };
  const { t } = useTranslation();
  return (
    <motion.button 
      className="pg-btn" 
      onClick={onCopy}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      {copied ? t('promptGuide:buttons.copied') : t('promptGuide:buttons.copy')}
    </motion.button>
  );
};

const CodeBox: React.FC<{ text: string }> = ({ text }) => (
  <div className="pg-code">
    <pre>{text}</pre>
  </div>
);

// ⬇компонент плавающей кнопки
const CopyFloating: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = React.useState(false);
  const onCopy = async () => {
    try { 
      await navigator.clipboard.writeText(text); 
      setCopied(true); 
      setTimeout(() => setCopied(false), 900);
    } catch {}
  };
  const { t } = useTranslation();
  return (
    <button className="pg-btn pg-copy-floating" onClick={onCopy}>
      {copied ? t('promptGuide:buttons.copied') : t('promptGuide:buttons.copy')}
    </button>
  );
};

const ExampleCard: React.FC<{ item: ExampleItem }> = ({ item }) => {
  const handleOpenImage = () => {
    window.open(item.img, '_blank', 'noopener,noreferrer')
  }

  const { t } = useTranslation();
  const verdictRaw = t(`promptGuide:params.examplesData.${item.id}.verdict`, { returnObjects: true, defaultValue: [] }) as unknown
  const verdict = (Array.isArray(verdictRaw) ? verdictRaw : verdictRaw ? [String(verdictRaw)] : []) as string[]

  const fixRaw = t(`promptGuide:params.examplesData.${item.id}.fix`, { returnObjects: true, defaultValue: [] }) as unknown
  const fix = (Array.isArray(fixRaw) ? fixRaw : fixRaw ? [String(fixRaw)] : []) as string[]

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      whileHover={{ y: -4 }}
      className="pg-card"
    >
      <div className="pg-image-wrap">
        {/* eslint-disable-next-line jsx-a11y/alt-text, @next/next/no-img-element */}
        <img src={item.img} className="pg-image" />
        <span
          className={
            "pg-badge " + (item.variant === "good" ? "pg-badge-good" : "pg-badge-bad")
          }
        >
          {item.variant === "good" ? t('promptGuide:examples.badge.good') : t('promptGuide:examples.badge.bad')}
        </span>
        <button 
          className="pg-image-open"
          onClick={handleOpenImage}
          title={t('promptGuide:buttons.openFull')}
        >
          {t('promptGuide:buttons.open')}
        </button>
      </div>
    <div className="pg-card-body">
      <CopyFloating text={item.prompt} />
      <div className="pg-card-title">
        {t(`promptGuide:params.examplesData.${item.id}.title`)}
      </div>
      <div className="pg-muted">{t('promptGuide:examples.labels.refAndPrompt')}</div>
      <CodeBox text={item.prompt} />
      <div className="pg-subtitle">
        {item.variant === "good" ? t('promptGuide:examples.labels.whatWorked') : t('promptGuide:examples.labels.whatsWrong')}
      </div>
      <ul className="pg-list">
        {verdict.map((v, i) => <li key={i}>{v}</li>)}
      </ul>
      {item.variant === 'bad' && fix.length > 0 && (
        <>
          <div className="pg-subtitle">{t('promptGuide:examples.labels.fix')}</div>
          <ul className="pg-list">
            {fix.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </>
      )}
    </div>
    </motion.div>
  );
};

const QUICK_TEMPLATES = {
  portrait: `portrait, cinematic, 85mm, subject-centered, natural skin, soft rim light, detailed eyes
clothing: formal dress, tasteful styling
background: shallow depth of field bokeh
lighting: soft key + subtle rim
quality: 4k, high detail`,
  fullBody: `full body, neutral angle, balanced proportions, elegant wardrobe
pose: standing or seated, legs crossed, hands relaxed
composition: rule of thirds, headroom, no cropping of limbs
quality: sharp focus, clean edges, filmic color`,
  environment: `interior grand hall, marble floor, chandeliers, volumetric light beams
subject: lone figure mid-frame, dress flows, heels
color palette: warm gold + cool neutrals
shot: wide angle 28mm, symmetrical composition`,
  fixers: `avoid: explicit nudity, micro-bikinis, fetish wear, exaggerated anatomy
prefer: tasteful fashion, realistic proportions, elegant silhouettes
ban: cropped heads, blown highlights, plastic skin, cluttered backgrounds`,
} as const;

const EXAMPLES: ExampleItem[] = [
  {
    id: "good-01",
    variant: "good",
    img: IMG.good.cinematicHall,
    prompt:
      "anime style, cinematic grand hall, marble floor, chandeliers, elegant woman in white evening dress, full body, neutral angle, soft golden light, realistic proportions, tasteful styling",
  },
  {
    id: "good-02",
    variant: "good",
    img: IMG.good.dominant_woman,
    prompt:
      "best quality, masterpiece, nsfw, big breasts, crossed legs, sheer tights",
  },
  {
    id: "good-03",
    variant: "good",
    img: IMG.good.girl_in_bedroom,
    prompt:
      "best quality, bedroom night, tall woman, nightgown, sheer tights, crossed legs, dominant, nsfw",
  },
  {
    id: "bad-01",
    variant: "bad",
    img: IMG.bad.bad_heels,
    prompt: "high heels",
  },
  {
    id: "bad-02",
    variant: "bad",
    img: IMG.bad.bad_dominance,
    prompt: "masterpiece, ultra high quality, anime illustration of two tall women in a golden throne room with chandeliers and banners, one of them wearing a silky black gown with a slit and sheer black tights while the other has blonde hair and a crimson gown, they are both crossing their legs elegantly while looking down with smug expressions at a shorter man who is kneeling submissively on the floor in front of them, the whole atmosphere is dramatic with warm golden lighting and shadows and the perspective is slightly from below to emphasize their power difference",
  },
  {
    id: "bad-03",
    variant: "bad",
    img: IMG.bad.bad_woman,
    prompt: "neon pinup, tight mini dress, cleavage focus",
  },
];

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({
  title,
  children,
}) => (
  <motion.section 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.4, ease: 'easeOut' }}
    className="pg-section"
  >
    <h2 className="pg-h2">{title}</h2>
    {children}
  </motion.section>
);

const PromptGuide: React.FC = () => {
  const { t } = useTranslation();
  return (
    <motion.div 
      initial={{ opacity: 0, y: 12 }} 
      animate={{ opacity: 1, y: 0 }} 
      exit={{ opacity: 0, y: -12 }} 
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="pg-root"
    >
      {/* Hero */}
      <div className="pg-hero">
        <div className="pg-hero-inner">
          <div className="pg-hero-text">
            <h1 className="pg-h1">{t('promptGuide:hero.title')}</h1>
            <p className="pg-muted">
              {t('promptGuide:hero.subtitle')}
            </p>
            <div className="pg-pills">
              <Pill>{t('promptGuide:hero.pills.scene')}</Pill>
              <Pill>{t('promptGuide:hero.pills.realistic')}</Pill>
              <Pill>{t('promptGuide:hero.pills.tasteful')}</Pill>
            </div>
          </div>
          <div className="pg-hero-side">
            <div className="pg-note">
              <CopyFloating text={QUICK_TEMPLATES.portrait} />
              <div className="pg-note-title">{t('promptGuide:hero.quickTemplateTitle')}</div>
              <CodeBox text={QUICK_TEMPLATES.portrait} />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Start */}
      <Section title={t('promptGuide:sections.quickStart')}>
        <div className="pg-grid-4">
          {[
            { title: t('promptGuide:quickStart.scene.title'), bullets: t('promptGuide:quickStart.scene.bullets', { returnObjects: true }) as string[] },
            { title: t('promptGuide:quickStart.subject.title'), bullets: t('promptGuide:quickStart.subject.bullets', { returnObjects: true }) as string[] },
            { title: t('promptGuide:quickStart.light.title'), bullets: t('promptGuide:quickStart.light.bullets', { returnObjects: true }) as string[] },
            { title: t('promptGuide:quickStart.quality.title'), bullets: t('promptGuide:quickStart.quality.bullets', { returnObjects: true }) as string[] },
          ].map((b, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1, ease: 'easeOut' }}
              whileHover={{ y: -2 }}
              className="pg-card-simple"
            >
              <div className="pg-card-title">{b.title}</div>
              <ul className="pg-list">
                {b.bullets.map((t, k) => (
                  <li key={k}>{t}</li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* Templates */}
      <Section title={t('promptGuide:sections.templates')}>
        <div className="pg-grid-3">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={QUICK_TEMPLATES.portrait} />
            <div className="pg-card-title">{t('promptGuide:templates.portrait')}</div>
            <CodeBox text={QUICK_TEMPLATES.portrait} />
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={QUICK_TEMPLATES.fullBody} />
            <div className="pg-card-title">{t('promptGuide:templates.fullBody')}</div>
            <CodeBox text={QUICK_TEMPLATES.fullBody} />
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.2, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={QUICK_TEMPLATES.environment} />
            <div className="pg-card-title">{t('promptGuide:templates.environment')}</div>
            <CodeBox text={QUICK_TEMPLATES.environment} />
          </motion.div>
        </div>
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.3, ease: 'easeOut' }}
          whileHover={{ y: -2 }}
          className="pg-card-simple" 
          style={{ marginTop: 12 }}
        >
          <CopyFloating text={QUICK_TEMPLATES.fixers} />
          <div className="pg-card-title">{t('promptGuide:templates.fixers')}</div>
          <CodeBox text={QUICK_TEMPLATES.fixers} />
        </motion.div>
      </Section>

      {/* Examples */}
      <Section title={t('promptGuide:sections.examples')}>
        <div className="pg-muted pg-examples-lead">
          {t('promptGuide:examples.lead')}
        </div>
        <div className="pg-grid-3">
          {EXAMPLES.map((ex) => (
            <ExampleCard key={ex.id} item={ex} />
          ))}
        </div>
      </Section>

      {/* Do/Don't */}
      <Section title={t('promptGuide:sections.doDont')}>
        <div className="pg-grid-2">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple pg-card-green"
          >
            <div className="pg-card-title">{t('promptGuide:do.title')}</div>
            <ul className="pg-list">
              {(t('promptGuide:do.list', { returnObjects: true }) as string[]).map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple pg-card-red"
          >
            <div className="pg-card-title">{t('promptGuide:dont.title')}</div>
            <ul className="pg-list">
              {(t('promptGuide:dont.list', { returnObjects: true }) as string[]).map((x, i) => <li key={i}>{x}</li>)}
            </ul>
          </motion.div>
        </div>
      </Section>

      {/* Troubleshooting */}
      <Section title={t('promptGuide:sections.troubleshooting')}>
        <motion.details 
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: 0, ease: 'easeOut' }}
          className="pg-details"
        >
          <summary>{t('promptGuide:troubleshooting.items.0.title')}</summary>
          <div className="pg-muted">{t('promptGuide:troubleshooting.items.0.text')}</div>
        </motion.details>
        <motion.details 
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: 0.1, ease: 'easeOut' }}
          className="pg-details"
        >
          <summary>{t('promptGuide:troubleshooting.items.1.title')}</summary>
          <div className="pg-muted">{t('promptGuide:troubleshooting.items.1.text')}</div>
        </motion.details>
        <motion.details 
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: 0.2, ease: 'easeOut' }}
          className="pg-details"
        >
          <summary>{t('promptGuide:troubleshooting.items.2.title')}</summary>
          <div className="pg-muted">{t('promptGuide:troubleshooting.items.2.text')}</div>
        </motion.details>
        <motion.details 
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: 0.3, ease: 'easeOut' }}
          className="pg-details"
        >
          <summary>{t('promptGuide:troubleshooting.items.3.title')}</summary>
          <div className="pg-muted">{t('promptGuide:troubleshooting.items.3.text')}</div>
        </motion.details>
      </Section>

      {/* Parameters Guide */}
      <Section title={t('promptGuide:sections.params')}>
        <div className="pg-muted pg-examples-lead">{t('promptGuide:params.lead')}</div>
        
        <div className="pg-grid-2">
          {/* Негативный промпт */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text="low quality, blurry, distorted, deformed, ugly, bad anatomy, bad proportions, extra limbs, missing limbs, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, extra fingers, missing fingers, extra arms, missing arms, extra legs, missing legs, malformed limbs, long neck, cross-eyed, mutated, bad anatomy, bad proportions, gross proportions, text, error, missing, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry" />
            <div className="pg-card-title">{t('promptGuide:params.negative.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.negative.desc')}
            </div>
            <CodeBox text="low quality, blurry, distorted, deformed, ugly, bad anatomy, bad proportions, extra limbs, missing limbs, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, extra fingers, missing fingers, extra arms, missing arms, extra legs, missing legs, malformed limbs, long neck, cross-eyed, mutated, bad anatomy, bad proportions, gross proportions, text, error, missing, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry" />
            <div className="pg-subtitle">{t('promptGuide:params.negative.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.negative.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>

          {/* Шаги */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={t('promptGuide:params.steps.code')} />
            <div className="pg-card-title">{t('promptGuide:params.steps.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.steps.desc')}
            </div>
            <CodeBox text={t('promptGuide:params.steps.code')} />
            <div className="pg-subtitle">{t('promptGuide:params.steps.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.steps.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>

          {/* CFG Scale */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.2, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={t('promptGuide:params.cfg.code')} />
            <div className="pg-card-title">{t('promptGuide:params.cfg.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.cfg.desc')}
            </div>
            <CodeBox text={t('promptGuide:params.cfg.code')} />
            <div className="pg-subtitle">{t('promptGuide:params.cfg.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.cfg.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>

          {/* Размеры */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.3, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={t('promptGuide:params.sizes.code')} />
            <div className="pg-card-title">{t('promptGuide:params.sizes.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.sizes.desc')}
            </div>
            <CodeBox text={t('promptGuide:params.sizes.code')} />
            <div className="pg-subtitle">{t('promptGuide:params.sizes.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.sizes.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>

          {/* Ref Image */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.4, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={t('promptGuide:params.refImage.code')} />
            <div className="pg-card-title">{t('promptGuide:params.refImage.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.refImage.desc')}
            </div>
            <CodeBox text={t('promptGuide:params.refImage.code')} />
            <div className="pg-subtitle">{t('promptGuide:params.refImage.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.refImage.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>

          {/* Seed */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.5, ease: 'easeOut' }}
            whileHover={{ y: -2 }}
            className="pg-card-simple"
          >
            <CopyFloating text={t('promptGuide:params.seed.code')} />
            <div className="pg-card-title">{t('promptGuide:params.seed.title')}</div>
            <div className="pg-muted" style={{ marginBottom: '12px' }}>
              {t('promptGuide:params.seed.desc')}
            </div>
            <CodeBox text={t('promptGuide:params.seed.code')} />
            <div className="pg-subtitle">{t('promptGuide:params.seed.subtitle')}</div>
            <ul className="pg-list">
              {(t('promptGuide:params.seed.list', { returnObjects: true }) as string[]).map((x,i)=><li key={i}>{x}</li>)}
            </ul>
          </motion.div>
        </div>
      </Section>

      </motion.div>
    );
  };

export default PromptGuide;
