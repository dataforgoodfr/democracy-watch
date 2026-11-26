// tag.types.ts

export type TagSize = 'sm' | 'md'

/* ---------- Aiguillages réutilisables ---------- */

// Section "Icon" : si hasIcon = true, icon est obligatoire
type TagIcon =
  | { hasIcon: true; icon: string }
  | { hasIcon?: false }

// Section "Attributes" : si blank = true, title est obligatoire (règle DSFR)
type TagLinkTarget =
  | { blank: true; attributes: { title: string } }
  | { blank?: false; attributes?: { title?: string } }

/* ---------- Champs communs ---------- */

type TagBase = {
  label: string
  size?: TagSize
}

/* ---------- Variantes ---------- */

export type DefaultTag = {
  type: 'default'
} & TagIcon

export type ClickableTag = {
  type: 'clickable'
  href: string
  accent?: string
  disabled?: boolean
} & TagLinkTarget & TagIcon

export type SelectableTag = {
  type: 'selectable'
  pressed: boolean
  disabled?: boolean
} & TagIcon

export type DeletableTag = {
  type: 'deletable'
  disabled?: boolean
}

/* ---------- Type final ---------- */

export type TagVariant = DefaultTag | ClickableTag | SelectableTag | DeletableTag
export type TagProps = TagBase & TagVariant
export type TagType = TagVariant['type'] // 'default' | 'clickable' | 'selectable' | 'deletable'
