"use client";

import { Logo } from "@democracy-watch/brand";
import { useSessionStore } from "@democracy-watch/state";
import { asString, Link, type QueryParams, useNavigation } from "@democracy-watch/ui";
import { Button, Checkbox, Divider, PasswordInput, TextInput } from "@mantine/core";
import { IconBell, IconFilter, IconMail, IconUsers } from "@tabler/icons-react";
import type { FormEvent } from "react";
import classes from "../screens.module.css";

const BENEFITS = [
  { Icon: IconBell, text: "Suivre les amendements d'un texte, article par article" },
  { Icon: IconFilter, text: "Filtrer ceux qui touchent vos sujets" },
  { Icon: IconUsers, text: "Repérer les acteurs derrière chaque proposition" },
];

/** Page vers laquelle revenir après connexion (chemin interne uniquement). */
const safeNext = (value: string) =>
  value.startsWith("/") && !value.startsWith("//") ? value : "/";

/**
 * Connexion (maquette « connexion »). V0 : session de démonstration, sans vérification du mot de
 * passe. « Rester connecté » choisit localStorage (persistant) plutôt que sessionStorage (onglet).
 */
export const LoginScreen = ({ params = {} }: { params?: QueryParams }) => {
  const { navigate } = useNavigation();
  const signIn = useSessionStore((state) => state.signIn);
  const next = safeNext(asString(params.suite));

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    signIn(String(form.get("email") ?? ""), form.get("remember") === "on");
    navigate(next);
  };

  return (
    <div className={classes.login}>
      <section className={classes.loginBrand} aria-label="Democracy Watch">
        <Logo size={44} />
        <h1 className={classes.loginTitle}>Gardez un œil sur vos amendements</h1>
        <ul className={classes.benefits}>
          {BENEFITS.map(({ Icon, text }) => (
            <li key={text}>
              <Icon size={22} aria-hidden />
              {text}
            </li>
          ))}
        </ul>
      </section>
      <section className={classes.loginForm} aria-labelledby="titre-connexion">
        <h2 id="titre-connexion" className={classes.loginFormTitle}>
          Connexion
        </h2>
        <p className={classes.hint}>
          Espace réservé aux associations, ONG et équipes de plaidoyer.
        </p>
        <form onSubmit={onSubmit} className={classes.form}>
          <TextInput
            label="Adresse e-mail"
            name="email"
            type="email"
            autoComplete="email"
            required
          />
          <PasswordInput
            label="Mot de passe"
            name="password"
            autoComplete="current-password"
            required
          />
          <div className={classes.formRow}>
            <Checkbox label="Rester connecté" name="remember" />
            <Link href="/connexion">Mot de passe oublié ?</Link>
          </div>
          <Button type="submit" size="md" fullWidth>
            Se connecter
          </Button>
        </form>
        <Divider label="ou" labelPosition="center" my="lg" />
        <Button
          variant="outline"
          size="md"
          fullWidth
          leftSection={<IconMail size={18} aria-hidden />}
          disabled
        >
          Recevoir un lien de connexion par e-mail (bientôt)
        </Button>
        <p className={classes.hint}>
          Pas encore de compte ? <Link href="/connexion">Créer un compte</Link>
        </p>
      </section>
    </div>
  );
};
