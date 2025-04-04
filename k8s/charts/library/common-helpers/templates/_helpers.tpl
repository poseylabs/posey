{{/* /k8s/charts/library/common-helpers/templates/_helpers.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* --- Common Helper Templates --- */}}

{{/*
Expand the name of the chart.
Usage: {{ include "common-helpers.name" . }}
*/}}
{{- define "common-helpers.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Usage: {{ include "common-helpers.fullname" . }}
*/}}
{{- define "common-helpers.fullname" -}}
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
Usage: {{ include "common-helpers.chart" . }}
*/}}
{{- define "common-helpers.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
Usage: {{ include "common-helpers.labels" . | nindent 4 }}
*/}}
{{- define "common-helpers.labels" -}}
helm.sh/chart: {{ include "common-helpers.chart" . }}
{{ include "common-helpers.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- /* Add global labels from values if defined */}}
{{- with .Values.global.commonLabels }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}

{{/*
Selector labels.
Usage: {{ include "common-helpers.selectorLabels" . }}
*/}}
{{- define "common-helpers.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common-helpers.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- /* Infer part-of label from chart path or allow override */}}
{{- $partOf := .Values.global.partOf | default (include "common-helpers.inferPartOf" .) }}
{{- if $partOf }}
app.kubernetes.io/part-of: {{ $partOf }}
{{- end }}
{{- end }}

{{/*
Helper to infer the 'part-of' label from the chart's path (e.g., k8s/charts/services/data -> posey-data)
Usage: {{ include "common-helpers.inferPartOf" . }}
*/}}
{{- define "common-helpers.inferPartOf" -}}
{{- $pathParts := splitList "/" .Chart.Name -}}
{{- if gt (len $pathParts) 2 -}}
  {{- $category := index $pathParts (sub (len $pathParts) 2) -}}
  {{- if eq $category "data" "services" "apps" -}}
    {{- printf "posey-%s" $category -}}
  {{- end -}}
{{- else -}}
  {{- /* If no path info, use the chart name as the category */}}
  {{- printf "posey-%s" .Chart.Name -}}
{{- end -}}
{{- end -}}

{{/*
Create the name of the service account to use
Usage: {{ include "common-helpers.serviceAccountName" . }}
*/}}
{{- define "common-helpers.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name | quote -}}
{{- else -}}
{{- if .Values.serviceAccount.create -}}
{{- include "common-helpers.fullname" . -}}
{{- else -}}
{{- "default" -}}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate image name based on global and local values.
It prioritizes the tag passed via Argo CD Helm parameters (.Values.parameters.image.tag),
then checks the chart's values file (.Values.image.tag), and finally defaults to 'latest'.
It uses the global registry value passed in via ApplicationSet/Helm parameters or values
(.Values.global.image.registry) or defaults to 'docker.io/poseylabs'.
The image repository must be defined in the chart's values (.Values.image.repository).

Usage: {{ include "common-helpers.image" . }}
*/}}
{{- define "common-helpers.image" -}}
{{- $registry := .Values.global.image.registry | default "docker.io/poseylabs" -}}
{{- $repository := .Values.image.repository -}}
{{- if not $repository -}}
  {{- fail (printf "%s: image.repository is required in values.yaml for chart %s" (include "common-helpers.fullname" .) .Chart.Name) -}}
{{- end -}}
{{- $tag := "" -}}
{{- /* Prioritize tag from Argo CD parameters if available */ -}}
{{- if .Values.parameters -}}
  {{- with .Values.parameters.image -}}
    {{- $tag = .tag | default "" -}}
  {{- end -}}
{{- end -}}
{{- /* Fallback to chart's image tag value */ -}}
{{- if not $tag -}}
  {{- $tag = .Values.image.tag | default "" -}}
{{- end -}}
{{- /* Default to 'latest' if no tag is specified anywhere */ -}}
{{- $tag = $tag | default "latest" -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- end -}}

{{/* --- End Common Helper Templates --- */}} 