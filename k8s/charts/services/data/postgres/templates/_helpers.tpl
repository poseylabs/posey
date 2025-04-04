{{/* /k8s/charts/services/data/postgres/templates/_helpers.tpl */}}
{{/* vim: set filetype=mustache: */}}

{{/* --- Postgres Specific Helper Templates --- */}}

{{/*
Create the name of the service account to use. 
This remains specific because the common helper only provides "default".
*/}}
{{- define "postgres.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- /* Use fullname if creating, but allow override */ -}}
{{- default (include "common-helpers.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- /* Use specific name from values if not creating, else default */ -}}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* --- End Postgres Specific Helper Templates --- */}}

{{/* --- Removed Duplicated Helpers --- */}}
{{/* 
'postgres.name', 'postgres.fullname', 'postgres.chart', 'postgres.labels', 
'postgres.selectorLabels', and 'postgres.image' helpers were removed. 
Use the equivalents from the 'common-helpers' library chart instead.
Example: {{ include "common-helpers.fullname" . }}
Example: {{ include "common-helpers.labels" . | nindent 4 }}
Example: {{ include "common-helpers.selectorLabels" . }}
Example: {{ include "common-helpers.image" . }}
*/}} 