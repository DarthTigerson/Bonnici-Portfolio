export interface SocialLink {
  enabled: boolean
  url: string
}

export interface MainInfo {
  name: string
  job_title: string
}

export interface ContactCard {
  social_links: {
    github: SocialLink
    linkedin: SocialLink
  }
}

export interface AboutMe {
  short_description: string
  long_description: string
}

export interface PanelFlag {
  enabled: boolean
  text: string
}

export interface WhatImDoingPanel {
  enabled: boolean
  title: string
  description: string
  image: string
  flag: PanelFlag
}

export interface Skill {
  title: string
  image: string
  background_color: string
  border_color: string
  is_new: boolean
}

export interface SkillSection {
  title: string
  skills: Skill[]
}

export interface Skills {
  sections: Record<string, SkillSection>
}

export interface Project {
  title: string
  image: string
  image_url?: string
  category: string
  tags: string[]
  description: string
  git_url: string
}

export interface Portfolio {
  enabled: boolean
  columns: 2 | 3
  mode: 'tags' | 'description'
  projects: Project[]
}

export interface Config {
  main_info: MainInfo
  contact_card: ContactCard
  about_me: AboutMe
  what_im_doing: Record<string, WhatImDoingPanel>
  skills: Skills
  portfolio: Portfolio
}
