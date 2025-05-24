{{- define "token-tally.name" -}}
{{ include "chart.name" . }}
{{- end -}}

{{- define "token-tally.fullname" -}}
{{ include "chart.name" . }}-{{ .Release.Name }}
{{- end -}}
