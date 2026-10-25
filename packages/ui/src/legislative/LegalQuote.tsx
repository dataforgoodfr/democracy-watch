import { Highlight } from "../core/Highlight.tsx";
import classes from "./legislative.module.css";

/** Extrait juridique en Spectral, avec sa référence (« — Art. 3, al. 4 »). */
export const LegalQuote = ({
  text,
  reference,
  highlight = [],
}: {
  text: string;
  reference: string;
  highlight?: readonly string[];
}) => (
  <blockquote className={`dw-loi ${classes.quote}`}>
    « <Highlight text={text} stems={highlight} /> » — {reference}
  </blockquote>
);
