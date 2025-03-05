declare -a gcp_variables=("GCP_TYPE" "GCP_PROJECT_ID" "GCP_PRIVATE_KEY_ID" "GCP_PRIVATE_KEY" "GCP_CLIENT_EMAIL" "GCP_CLIENT_ID" "GCP_AUTH_URI" "GCP_TOKEN_URI" "GCP_AUTH_PROVIDER" "GCP_CLIENT_CERT")

declare -a ee_variables=("type" "project_id" "private_key_id" "private_key" "client_email" "client_id" "auth_uri" "token_uri" "auth_provider_x509_cert_url" "client_x509_cert_url")

declare -A variables

for ((i=0; i<${#gcp_variables[@]}; i++)); do
  var_gcp="${gcp_variables[$i]}"
  var_ee="${ee_variables[$i]}"
  variables["$var_ee"]=$var_gcp
done

json_string="{"
for key in "${!variables[@]}"; do
  json_string+=" \"$key\": \"${variables[$key]}\""
  if [[ $key != "${!variables[@]}" ]]; then
    printf -v json_string '%s,\n' "$json_string"
  fi
done


json_string="${json_string%,*} }"

echo "$json_string" > GCP_credentials.json

conda install -c conda-forge gdal=3.9.3 -y
pip install -r requirements.txt --no-cache-dir