/**
 * Écrans de l'application. Chaque écran reçoit les paramètres de sa route et charge ses données
 * via les hooks de @democracy-watch/api. Le site Next.js ne fait que relier une route à un écran.
 */
export { AddTextsScreen } from "./add-texts/AddTextsScreen.tsx";
export { addTextsParamsOf, parseAddTextsParams } from "./add-texts/params.ts";
export { FollowedAmendmentsScreen } from "./amendments/FollowedAmendmentsScreen.tsx";
export { amendmentParamsOf, parseAmendmentParams } from "./amendments/params.ts";
export { ArticleScreen } from "./article/ArticleScreen.tsx";
export { articleParamsOf, parseArticleParams } from "./article/params.ts";
export { LoginScreen } from "./auth/LoginScreen.tsx";
export { HomeScreen } from "./home/HomeScreen.tsx";
export { AppLayout } from "./layout/AppLayout.tsx";
export { NotFoundScreen } from "./not-found/NotFoundScreen.tsx";
export { parseSearchParams, searchParamsOf } from "./search/params.ts";
export { SearchScreen } from "./search/SearchScreen.tsx";
export { MyTextsScreen } from "./texts/MyTextsScreen.tsx";
export { TextScreen } from "./texts/TextScreen.tsx";
