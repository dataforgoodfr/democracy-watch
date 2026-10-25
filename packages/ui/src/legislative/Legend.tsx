import classes from "./legislative.module.css";

/** Légende de la vue « avancement ». */
export const Legend = () => (
  <ul className={classes.legend} aria-label="Légende">
    <li>
      <span className={classes.legendSimilar} aria-hidden /> Bordure sarcelle = appartient à un
      groupe d'amendements similaires
    </li>
    <li>
      <span className={classes.probable}>↪</span> = lien probable entre étapes, à confirmer
    </li>
    <li>
      <span className={classes.legendUpcoming} aria-hidden /> Colonne orangée = prochaine échéance
    </li>
  </ul>
);
