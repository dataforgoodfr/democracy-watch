"use client";

import { Alert, Button, Skeleton } from "@mantine/core";
import { IconAlertTriangle, IconRefresh } from "@tabler/icons-react";
import classes from "./core.module.css";

/** Chargement : lignes squelettes annoncées aux lecteurs d'écran. */
export const LoadingState = ({
  lines = 3,
  label = "Chargement…",
}: {
  lines?: number;
  label?: string;
}) => (
  <div className={classes.loading} role="status" aria-live="polite" aria-busy="true">
    <span className="dw-visually-hidden">{label}</span>
    {Array.from({ length: lines }, (_, line) => (
      <Skeleton key={`ligne-${line + 1}`} height={line === 0 ? 24 : 72} radius="md" />
    ))}
  </div>
);

type ErrorStateProps = {
  title?: string;
  message?: string;
  onRetry?: () => void;
};

/** Erreur récupérable (source indisponible, réseau) avec « Réessayer ». */
export const ErrorState = ({
  title = "Données momentanément indisponibles",
  message = "La source n'a pas répondu. Vos textes suivis sont conservés.",
  onRetry,
}: ErrorStateProps) => (
  <Alert
    color="red"
    variant="light"
    icon={<IconAlertTriangle size={20} aria-hidden />}
    title={title}
    role="alert"
  >
    <p className={classes.errorMessage}>{message}</p>
    {onRetry ? (
      <Button
        size="xs"
        variant="outline"
        color="red"
        leftSection={<IconRefresh size={14} aria-hidden />}
        onClick={onRetry}
      >
        Réessayer
      </Button>
    ) : null}
  </Alert>
);
