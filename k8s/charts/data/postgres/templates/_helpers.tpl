{{/* /k8s/charts/data/postgres/templates/_helpers.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* Define chart-specific helpers here if needed */}}

{{/*
Return the appropriate image name for the Postgres chart.
It prioritizes the tag passed via Argo CD Helm parameters,
then checks the chart's values file, and finally defaults to 'latest'.
It uses the global registry value passed in via ApplicationSet/Helm parameters or values.
Usage: {{ include "postgres.image" . }}
*/}}
{{- define "postgres.image" -}}
{{- $registry := .Values.global.image.registry | default "docker.io/poseylabs" }}
{{- $repository := .Values.image.repository }}
{{- if not $repository }}
  {{- fail "postgres.image: image.repository is required in values.yaml" }}
{{- end }}
{{/* Prioritize tag from Argo CD parameters if they exist */}}
{{- $tag := "" }}
{{- if .Values.parameters }}
  {{- with .Values.parameters.image }} {{/* Check if parameters.image exists */}}
    {{- $tag = .tag | default "" }}
  {{- end }}
{{- end }}
{{/* If not found in parameters, check chart values */}}
{{- if not $tag }}
  {{- $tag = .Values.image.tag | default "" }}
{{- end }}
{{/* If still not found, default to 'latest' */}}
{{- $tag = $tag | default "latest" }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}

{{/* Other postgres-specific helpers could go here */}}

{{/*
Expand the name of the chart.
*/}}
{{- define "postgres.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "postgres.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "postgres.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "postgres.labels" -}}
helm.sh/chart: {{ include "postgres.chart" . }}
{{ include "postgres.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "postgres.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/part-of: posey-data # Or make this configurable if needed
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "postgres.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "postgres.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }} 