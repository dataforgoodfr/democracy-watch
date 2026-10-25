// Fondations
export { Badge, type BadgeTone } from "./core/Badge.tsx";
export { Card } from "./core/Card.tsx";
export { EmptyState } from "./core/EmptyState.tsx";
export { Highlight, highlightSegments } from "./core/Highlight.tsx";
export { asArray, asString, buildHref, type QueryParams, toggle } from "./core/href.ts";
export {
  Link,
  type LinkProps,
  type Navigation,
  NavigationProvider,
  useNavigation,
} from "./core/navigation.tsx";
export { ErrorState, LoadingState } from "./core/QueryStates.tsx";
// Filtres et navigation locale
export { type FilterGroup, type FilterOption, FilterPanel } from "./filters/FilterPanel.tsx";
export { type Pill, Pills } from "./filters/Pills.tsx";
export { type AmendmentView, ViewSwitcher } from "./filters/ViewSwitcher.tsx";
// Mise en page
export { AppShell, type NavItem } from "./layout/AppShell.tsx";
export { GlobalSearch } from "./layout/GlobalSearch.tsx";
export { Breadcrumb, type Crumb, PageHeader, SectionHeader } from "./layout/PageHeader.tsx";
// Législatif
export { AmendmentCard } from "./legislative/AmendmentCard.tsx";
export { AmendmentRow, AuthorLine } from "./legislative/AmendmentRow.tsx";
export { ArticleRow } from "./legislative/ArticleRow.tsx";
export {
  AmendmentStatusBadge,
  CommissionBadge,
  GroupDot,
  SourceBadge,
  StudyBadge,
  TextTypeBadge,
} from "./legislative/badges.tsx";
export { daysUntil, formatDate, plural } from "./legislative/format.ts";
export { LegalQuote } from "./legislative/LegalQuote.tsx";
export { Legend } from "./legislative/Legend.tsx";
export { LegislativeTextCard } from "./legislative/LegislativeTextCard.tsx";
export { StageColumn } from "./legislative/StageColumn.tsx";
export { TextsTable } from "./legislative/TextsTable.tsx";
