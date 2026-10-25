import { Fragment } from "react";
import classes from "./core.module.css";

const normalize = (value: string) =>
  value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

/**
 * Découpe `text` en segments, en marquant les mots qui commencent par l'une des racines.
 * Texte et racines sont comparés sans accents ni majuscules. `start` (position) sert de clé stable.
 */
export const highlightSegments = (text: string, stems: readonly string[]) => {
  const normalizedStems = stems.map(normalize);
  let start = 0;
  return text.split(/(\p{L}+)/u).map((part) => {
    const segment = {
      text: part,
      start,
      match:
        normalizedStems.length > 0 &&
        /\p{L}/u.test(part) &&
        normalizedStems.some((stem) => normalize(part).startsWith(stem)),
    };
    start += part.length;
    return segment;
  });
};

/** Surligne les termes recherchés (sarcelle texte, gras souligné). */
export const Highlight = ({ text, stems }: { text: string; stems: readonly string[] }) => (
  <>
    {highlightSegments(text, stems).map((segment) =>
      segment.match ? (
        <mark key={segment.start} className={classes.highlight}>
          {segment.text}
        </mark>
      ) : (
        <Fragment key={segment.start}>{segment.text}</Fragment>
      ),
    )}
  </>
);
