#!/bin/sh

PI_PACKAGE="@earendil-works/pi-coding-agent"
PI_CMD="pi"
PI_INSTALLER_API_BASE="${PI_INSTALLER_API_BASE:-https://pi.dev/api/installer/releases}"
# Pi publishes npm-shrinkwrap.json, so the explicit installer/reinstaller can
# bypass npm's release-age gate without reopening transitive dependency ranges.
PI_NPM_INSTALL_MIN_AGE_ARG="--min-release-age=0"
PI_ESC=$(printf '\033')
PI_CR=$(printf '\r')
readonly PI_PACKAGE PI_CMD PI_INSTALLER_API_BASE PI_NPM_INSTALL_MIN_AGE_ARG PI_ESC PI_CR

pi_installer_main() {
  set -eu

  check_file="${TMPDIR:-/tmp}/pi-installer-checks.$$"
  run_preflight_checks >"$check_file" &
  check_pid=$!

  pi_logo_animation

  if wait "$check_pid"; then
    check_status=0
  else
    check_status=$?
  fi

  printf '\033[1m  Pi Installer\033[0m\n\033[2m  There are many coding agents, but this one is mine.\033[0m\n\n'
  if [ "$check_status" -eq 0 ]; then
    cat "$check_file"
  fi
  rm -f "$check_file"

  if [ "$check_status" -ne 0 ]; then
    if ! install_node_npm_interactive; then
      exit "$check_status"
    fi

    check_file="${TMPDIR:-/tmp}/pi-installer-checks.$$"
    if run_preflight_checks >"$check_file"; then
      check_status=0
    else
      check_status=$?
    fi
    cat "$check_file"
    rm -f "$check_file"

    if [ "$check_status" -ne 0 ]; then
      exit "$check_status"
    fi
  fi

  PI_EXISTING_PATH=$(command -v "$PI_CMD" 2>/dev/null || true)
  export PI_EXISTING_PATH

  if ! PI_NPM_INSTALL_PREFIX=$(select_npm_install_prefix); then
    exit 1
  fi
  export PI_NPM_INSTALL_PREFIX

  PI_NPM_UNINSTALL_PREFIX=$(select_npm_uninstall_prefix "$PI_EXISTING_PATH")
  export PI_NPM_UNINSTALL_PREFIX

  choose_pi_action "$PI_EXISTING_PATH"
  case "$PI_INSTALL_ACTION" in
    uninstall)
      uninstall_pi_package
      printf '\nPi was uninstalled successfully.\n'
      exit 0
      ;;
    none)
      exit 0
      ;;
  esac

  install_pi_package
  if [ "$PI_INSTALL_ACTION" = reinstall ]; then
    printf '\nPi was reinstalled successfully.\n'
  else
    printf '\nPi was installed successfully.\n'
  fi
  if installed_pi_is_first_on_path; then
    printf '\nRun it with: pi\n'
    if [ "${PI_NODE_INSTALLED_STANDALONE:-0}" = 1 ]; then
      printf 'If pi is not found in your shell yet, add this to your shell profile:\n\n'
      printf '  export PATH="%s:$PATH"\n' "$PI_STANDALONE_NODE_BIN"
    fi
  else
    print_pi_not_on_path_message
  fi

}

run_preflight_checks() {
  status=0

  if command -v node >/dev/null 2>&1; then
    node_version=$(node --version)
    if ! node -e 'const [maj,min,patch] = process.versions.node.split(".").map(Number); process.exit(maj > 22 || (maj === 22 && (min > 19 || (min === 19 && patch >= 0))) ? 0 : 1)' >/dev/null; then
      printf 'error: Pi requires Node.js 22.19.0 or newer. Found %s.\n' "$node_version"
      status=1
    fi
  else
    printf 'error: Node.js 22.19.0 or newer is required to install Pi.\n'
    status=1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    printf 'error: npm is required to install Pi.\n'
    status=1
  fi

  if [ "$status" -ne 0 ]; then
    printf '\n'
  fi

  return "$status"
}

install_node_npm_interactive() {
  method=$(detect_node_install_method)
  case "$method" in
    homebrew) label="Homebrew" ;;
    apt) label="apt" ;;
    apk) label="apk" ;;
    standalone) label="standalone Node.js" ;;
  esac

  if ! ( : <>/dev/tty ) 2>/dev/null; then
    printf 'No terminal detected; install Node.js 22.19.0 or newer and npm, then run this installer again.\n'
    return 1
  fi
  exec 3<>/dev/tty

  printf 'Pi needs Node.js 22.19.0 or newer and npm. Install them now with %s? [Y/n] ' "$label" >&3
  answer="Y"
  exec 3>&-
  case "$answer" in
    n|N|no|NO) printf '\nInstall Node.js 22.19.0 or newer and npm, then run this installer again.\n'; return 1 ;;
    *) ;;
  esac

  install_node_npm "$method" "$label"
}

detect_node_install_method() {
  case "$(uname -s)" in
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        printf 'homebrew'
      else
        printf 'standalone'
      fi
      ;;
    Linux)
      if command -v apt-cache >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1 && apt_node_candidate_is_new_enough; then
        printf 'apt'
      elif command -v apk >/dev/null 2>&1 && apk_node_candidate_is_new_enough; then
        printf 'apk'
      else
        printf 'standalone'
      fi
      ;;
    *)
      printf 'standalone'
      ;;
  esac
}

apt_node_candidate_is_new_enough() {
  version=$(apt-cache policy nodejs 2>/dev/null | awk '/Candidate:/ { print $2; exit }')
  [ -n "$version" ] && [ "$version" != "(none)" ] && node_version_string_is_new_enough "$version"
}

apk_node_candidate_is_new_enough() {
  version=$(apk search -x nodejs 2>/dev/null | awk -F- '/^nodejs-/ { print $2; exit }')
  [ -n "$version" ] && node_version_string_is_new_enough "$version"
}

node_version_string_is_new_enough() {
  version="${1#v}"
  case "$version" in
    [0-9]*) ;;
    *) return 1 ;;
  esac
  version="${version%%[!0-9.]*}"
  version_ifs=${IFS- }
  IFS=.
  set -- $version
  IFS=$version_ifs
  major="${1:-}"
  minor="${2:-0}"
  patch="${3:-0}"
  case "$major" in ''|*[!0-9]*) return 1 ;; esac
  case "$minor" in ''|*[!0-9]*) minor=0 ;; esac
  case "$patch" in ''|*[!0-9]*) patch=0 ;; esac

  [ "$major" -gt 22 ] && return 0
  [ "$major" -eq 22 ] && [ "$minor" -gt 19 ] && return 0
  [ "$major" -eq 22 ] && [ "$minor" -eq 19 ] && [ "$patch" -ge 0 ] && return 0
  return 1
}

install_node_npm() {
  method="$1"; label="$2"

  if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
    install_node_npm_with_progress "$method" "$label"
  else
    printf '\nInstalling Node.js and npm with %s...\n\n' "$label"
    run_node_install_method "$method"
    printf '\nNode.js and npm are installed.\n'
  fi

  if [ "$method" = standalone ]; then
    load_standalone_node
    PI_NODE_INSTALLED_STANDALONE=1
  fi
  hash -r
  printf '\n'
}

install_node_npm_with_progress() {
  method="$1"; label="$2"
  log_file="${TMPDIR:-/tmp}/pi-installer-node.$$"
  rm -f "$log_file"
  : >"$log_file"

  run_node_install_method "$method" >"$log_file" 2>&1 &
  install_pid=$!

  printf '\033[?25l'
  animate_node_install "$log_file" "$label" &
  progress_pid=$!
  trap 'kill "$install_pid" 2>/dev/null || true; finish_install_progress "$progress_pid"; exit 130' INT TERM

  if wait "$install_pid"; then
    status=0
  else
    status=$?
  fi

  finish_install_progress "$progress_pid"
  trap - INT TERM

  if [ "$status" -ne 0 ]; then
    printf '\033[31mNode.js installation failed.\033[0m\n\n'
    cat "$log_file"
    rm -f "$log_file"
    return "$status"
  fi

  rm -f "$log_file"
  if terminal_supports_unicode; then
    printf '  \033[32m✓\033[0m Node.js and npm install complete\n'
  else
    printf '  \033[32mok\033[0m Node.js and npm install complete\n'
  fi
}

run_node_install_method() {
  case "$1" in
    homebrew) install_node_with_homebrew ;;
    apt) install_node_with_apt ;;
    apk) install_node_with_apk ;;
    standalone) install_node_standalone ;;
  esac
}

install_node_with_homebrew() {
  if brew list node >/dev/null 2>&1; then
    brew upgrade node
  else
    brew install node
  fi
}

install_node_with_apt() {
  print_sudo_note
  if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    apt-get update
    apt-get install -y nodejs npm
  else
    sudo sh -c 'apt-get update && apt-get install -y nodejs npm'
  fi
}

install_node_with_apk() {
  print_sudo_note
  run_with_sudo apk add --update-cache nodejs npm
}

install_node_standalone() {
  node_platform=$(detect_node_binary_platform) || {
    printf 'Unsupported operating system for automatic Node.js install: %s\n' "$(uname -s)"
    return 1
  }
  node_arch=$(detect_node_binary_arch) || {
    printf 'Unsupported CPU architecture for automatic Node.js install: %s\n' "$(uname -m)"
    return 1
  }
  node_dist_base="https://nodejs.org/dist/latest-v22.x"
  node_base_dir=$(node_standalone_base_dir)
  node_tmp_dir="${TMPDIR:-/tmp}/pi-node.$$"

  rm -rf "$node_tmp_dir"
  mkdir -p "$node_tmp_dir" "$node_base_dir"

  printf 'Resolving Node.js binary for %s-%s\n' "$node_platform" "$node_arch"
  curl -fsSL "$node_dist_base/SHASUMS256.txt" -o "$node_tmp_dir/SHASUMS256.txt"
  node_file=$(awk -v suffix="-$node_platform-$node_arch.tar.xz" '
    index($2, "node-v") == 1 && length($2) >= length(suffix) && substr($2, length($2) - length(suffix) + 1) == suffix { print $2; exit }
  ' "$node_tmp_dir/SHASUMS256.txt")
  if [ -z "$node_file" ]; then
    printf 'No Node.js binary is available for %s-%s.\n' "$node_platform" "$node_arch"
    rm -rf "$node_tmp_dir"
    return 1
  fi

  printf 'Downloading Node.js %s\n' "${node_file%.tar.xz}"
  curl -fsSL "$node_dist_base/$node_file" -o "$node_tmp_dir/$node_file"
  verify_node_standalone_download "$node_tmp_dir" "$node_file"
  ensure_node_standalone_extract_tools "$node_platform"

  node_dir="$node_base_dir/${node_file%.tar.xz}"
  rm -rf "$node_dir"
  printf 'Extracting Node.js to %s\n' "$node_dir"
  tar -xf "$node_tmp_dir/$node_file" -C "$node_base_dir"
  rm -f "$node_base_dir/current"
  ln -s "$node_dir" "$node_base_dir/current"
  rm -rf "$node_tmp_dir"
  printf 'Node.js installed at %s\n' "$node_dir"
}

verify_node_standalone_download() {
  checksum_dir="$1"
  checksum_file_name="$2"
  awk -v file="$checksum_file_name" '$2 == file { print }' "$checksum_dir/SHASUMS256.txt" > "$checksum_dir/SHASUMS256.selected"

  if command -v sha256sum >/dev/null 2>&1; then
    printf 'Verifying Node.js download\n'
    (cd "$checksum_dir" && sha256sum -c SHASUMS256.selected)
  elif command -v shasum >/dev/null 2>&1; then
    printf 'Verifying Node.js download\n'
    (cd "$checksum_dir" && shasum -a 256 -c SHASUMS256.selected)
  fi
}

ensure_node_standalone_extract_tools() {
  extract_platform="$1"

  if [ "$extract_platform" = linux ] && ! command -v xz >/dev/null 2>&1; then
    printf 'Installing xz-utils for Node.js archive extraction\n'
    print_sudo_note
    if command -v apt-get >/dev/null 2>&1; then
      run_with_sudo apt-get update
      run_with_sudo apt-get install -y xz-utils
    elif command -v apk >/dev/null 2>&1; then
      run_with_sudo apk add --update-cache xz
    else
      printf 'xz is required to extract Node.js. Install xz and run this installer again.\n'
      return 1
    fi
  fi
}

load_standalone_node() {
  PI_STANDALONE_NODE_BIN="$(node_standalone_base_dir)/current/bin"
  PATH="$PI_STANDALONE_NODE_BIN:$PATH"
  export PI_STANDALONE_NODE_BIN PATH
}

node_standalone_base_dir() {
  if [ -n "${XDG_DATA_HOME:-}" ]; then
    printf '%s/pi-node' "$XDG_DATA_HOME"
  else
    printf '%s/.local/share/pi-node' "$HOME"
  fi
}

detect_node_binary_platform() {
  case "$(uname -s)" in
    Darwin) printf 'darwin' ;;
    Linux) printf 'linux' ;;
    *) return 1 ;;
  esac
}

detect_node_binary_arch() {
  case "$(uname -m)" in
    x86_64|amd64) printf 'x64' ;;
    arm64|aarch64) printf 'arm64' ;;
    armv7l) printf 'armv7l' ;;
    ppc64le) printf 'ppc64le' ;;
    s390x) printf 's390x' ;;
    *) return 1 ;;
  esac
}

print_sudo_note() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    printf 'This may ask for your sudo password.\n\n'
  fi
}

run_with_sudo() {
  if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

select_npm_install_prefix() {
  npm_prefix=$(npm_global_prefix)
  if [ -n "$npm_prefix" ] && npm_prefix_supports_global_install "$npm_prefix"; then
    return 0
  fi

  if existing_global_pi_blocks_user_local_install "$npm_prefix"; then
    print_existing_global_pi_not_writable_message "$npm_prefix"
    return 1
  fi

  printf '%s/.local' "$HOME"
}

select_npm_uninstall_prefix() {
  existing_pi_path="$1"
  [ -n "$existing_pi_path" ] || return 0

  npm_prefix=$(npm_global_prefix)
  if [ -n "$npm_prefix" ] && [ "$existing_pi_path" = "$npm_prefix/bin/$PI_CMD" ]; then
    return 0
  fi

  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ] && [ "$existing_pi_path" = "$PI_NPM_INSTALL_PREFIX/bin/$PI_CMD" ]; then
    printf '%s' "$PI_NPM_INSTALL_PREFIX"
    return 0
  fi

  pi_bin_suffix="/bin/$PI_CMD"
  case "$existing_pi_path" in
    *"$pi_bin_suffix") printf '%s' "${existing_pi_path%$pi_bin_suffix}" ;;
  esac
}

npm_global_prefix() {
  npm prefix -g 2>/dev/null || npm config get prefix 2>/dev/null
}

npm_prefix_supports_global_install() {
  prefix="$1"
  path_is_writable_or_creatable "$prefix/lib/node_modules" && path_is_writable_or_creatable "$prefix/bin"
}

existing_global_pi_blocks_user_local_install() {
  npm_prefix="$1"
  [ -n "$npm_prefix" ] || return 1

  [ -e "$npm_prefix/bin/$PI_CMD" ]
}

print_existing_global_pi_not_writable_message() {
  npm_prefix="$1"
  existing_pi_path="$npm_prefix/bin/$PI_CMD"

  printf "npm's global directory is not writable: %s\n" "$npm_prefix" >&2
  printf 'Pi is already installed at: %s\n\n' "$existing_pi_path" >&2
  printf 'Installing another copy under %s/.local could leave your shell using the old global pi, so this installer stopped.\n\n' "$HOME" >&2
  printf 'Update or remove the existing global install first. If it was installed with npm, you can run:\n\n' >&2
  printf '  sudo npm install -g --ignore-scripts %s %s\n\n' "$PI_NPM_INSTALL_MIN_AGE_ARG" "$PI_PACKAGE" >&2
  printf 'or uninstall it first with:\n\n' >&2
  printf '  sudo npm uninstall -g %s\n\n' "$PI_PACKAGE" >&2
  printf 'Then run this installer again.\n' >&2
}

path_is_writable_or_creatable() {
  check_path="$1"
  while [ ! -e "$check_path" ]; do
    parent=${check_path%/*}
    if [ -z "$parent" ] || [ "$parent" = "$check_path" ]; then
      return 1
    fi
    check_path="$parent"
  done

  [ -d "$check_path" ] && [ -w "$check_path" ]
}

pi_install_bin_dir() {
  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ]; then
    printf '%s/bin' "$PI_NPM_INSTALL_PREFIX"
  else
    npm_prefix=$(npm_global_prefix)
    if [ -n "$npm_prefix" ]; then
      printf '%s/bin' "$npm_prefix"
    fi
  fi
}

pi_installed_path() {
  pi_bin_dir=$(pi_install_bin_dir)
  if [ -n "$pi_bin_dir" ]; then
    printf '%s/%s' "$pi_bin_dir" "$PI_CMD"
  fi
}

installed_pi_is_first_on_path() {
  installed_pi_path=$(pi_installed_path)
  [ -n "$installed_pi_path" ] || return 1

  active_pi_path=$(command -v "$PI_CMD" 2>/dev/null) || return 1
  [ "$active_pi_path" = "$installed_pi_path" ]
}

shell_config_file() {
  current_shell=$(basename "${SHELL:-sh}")
  case "$current_shell" in
    fish) printf '%s/.config/fish/config.fish' "$HOME" ;;
    zsh) printf '%s/.zshrc' "${ZDOTDIR:-$HOME}" ;;
    bash)
      if [ -f "$HOME/.bashrc" ]; then
        printf '%s/.bashrc' "$HOME"
      else
        printf '%s/.profile' "$HOME"
      fi
      ;;
    *) printf '%s/.profile' "$HOME" ;;
  esac
}

path_update_command() {
  bin_dir="$1"
  current_shell=$(basename "${SHELL:-sh}")
  if [ "$bin_dir" = "$HOME/.local/bin" ]; then
    bin_expr='$HOME/.local/bin'
  else
    bin_expr="$bin_dir"
  fi

  case "$current_shell" in
    fish) printf 'fish_add_path "%s"' "$bin_expr" ;;
    *) printf 'export PATH="%s:$PATH"' "$bin_expr" ;;
  esac
}

config_file_mentions_path() {
  config_file="$1"
  command="$2"

  [ -f "$config_file" ] || return 1
  grep -Fxq "$command" "$config_file"
}

prompt_add_path_to_profile() {
  bin_dir="$1"
  if ! ( : <>/dev/tty ) 2>/dev/null; then
    return 1
  fi

  config_file=$(shell_config_file)
  command=$(path_update_command "$bin_dir")

  if config_file_mentions_path "$config_file" "$command"; then
    printf 'A PATH update for %s already exists in %s.\n' "$bin_dir" "$config_file"
    return 0
  fi

  exec 3<>/dev/tty
  printf 'Add %s to your PATH in %s now? [Y/n] ' "$bin_dir" "$config_file" >&3
  if ! IFS= read -r answer <&3; then
    answer=
  fi
  exec 3>&-
  case "$answer" in
    n|N|no|NO) return 1 ;;
    *) ;;
  esac

  mkdir -p "${config_file%/*}"
  touch "$config_file"
  printf '\n# Pi\n%s\n' "$command" >> "$config_file"
  printf 'Added %s to %s.\n' "$bin_dir" "$config_file"
}

print_pi_not_on_path_message() {
  pi_bin_dir=$(pi_install_bin_dir)
  active_pi_path=$(command -v "$PI_CMD" 2>/dev/null || true)

  printf 'Pi was installed, but your shell is not using that install yet.\n'
  if [ -n "$active_pi_path" ]; then
    printf 'Your shell currently resolves pi to: %s\n' "$active_pi_path"
  fi

  if [ -n "$pi_bin_dir" ]; then
    prompt_add_path_to_profile "$pi_bin_dir" || true
    command=$(path_update_command "$pi_bin_dir")
    printf 'Restart your shell or run:\n\n'
    printf '  %s\n\n' "$command"
    printf 'Then run: pi\n'
  else
    printf "Check npm's global prefix with:\n\n"
    printf '  npm prefix -g\n\n'
    printf 'Then add its bin directory to your shell PATH.\n'
  fi
}

choose_pi_action() {
  existing_pi_path="$1"

  if ! ( : <>/dev/tty ) 2>/dev/null; then
    print_pi_action_menu "$existing_pi_path"
    printf 'No terminal detected; continuing without confirmation.\n'
    PI_INSTALL_ACTION=install
    print_pi_action_selection "$PI_INSTALL_ACTION"
    return 0
  fi

  exec 3<>/dev/tty
  print_pi_action_menu "$existing_pi_path" >&3

  PI_INSTALL_ACTION=install
  print_pi_action_selection "$PI_INSTALL_ACTION" >&3
  exec 3>&-
}

print_pi_action_menu() {
  existing_pi_path="$1"

  reset=
  dim=
  bold=
  cyan=
  green=
  red=
  if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
    reset="${PI_ESC}[0m"
    dim="${PI_ESC}[2m"
    bold="${PI_ESC}[1m"
    cyan="${PI_ESC}[36m"
    green="${PI_ESC}[32m"
    red="${PI_ESC}[31m"
  fi

  if [ -n "$existing_pi_path" ]; then
    printf '%sPi is already installed at:%s\n\n' "$bold" "$reset"
    printf '  %s\n\n' "$existing_pi_path"
  fi

  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ]; then
    printf "npm's global directory is not writable; Pi will be installed under %s.\n\n" "$PI_NPM_INSTALL_PREFIX"
  fi

  if [ -n "$existing_pi_path" ]; then
    printf '%sReinstall command:%s\n\n  ' "$bold" "$reset"
  else
    printf '%sInstall command:%s\n\n  ' "$bold" "$reset"
  fi
  print_npm_install_command
  printf '\n\n'

  printf '%sChoose an action:%s\n\n' "$bold" "$reset"
  if [ -n "$existing_pi_path" ]; then
    printf '  %s%-4s%s %sReinstall Pi%s %s(default)%s\n' "$cyan" 'y' "$reset" "$green" "$reset" "$dim" "$reset"
    printf '  %s%-4s%s %sUninstall Pi%s\n' "$cyan" 'u' "$reset" "$red" "$reset"
  else
    printf '  %s%-4s%s %sInstall Pi%s %s(default)%s\n' "$cyan" 'y' "$reset" "$green" "$reset" "$dim" "$reset"
  fi
  printf '  %s%-4s%s %sDo nothing%s\n' "$cyan" 'n' "$reset" "$dim" "$reset"
}

print_pi_action_selection() {
  case "$1" in
    install) message="Will install Pi." ;;
    reinstall) message="Will reinstall Pi." ;;
    uninstall) message="Will uninstall Pi." ;;
    none) message="Chose to do nothing. Exiting." ;;
  esac
  printf '\n%s\n\n' "$message"
}

read_tty_key() {
  old_tty_state=$(stty -g < /dev/tty)
  trap 'stty "$old_tty_state" < /dev/tty; trap - INT TERM; exit 130' INT TERM
  stty -icanon -echo min 1 time 0 < /dev/tty
  if ! key=$(dd bs=1 count=1 2>/dev/null < /dev/tty); then
    key=
  fi
  stty "$old_tty_state" < /dev/tty
  trap - INT TERM
  printf '%s' "$key"
}

print_npm_install_command() {
  if pi_locked_install_enabled; then
    printf 'locked install from %s (fallback: ' "$PI_INSTALLER_API_BASE"
    print_npm_install_fallback_command
    printf ')'
  else
    print_npm_install_fallback_command
  fi
}

print_npm_install_fallback_command() {
  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ]; then
    printf 'npm install -g --ignore-scripts %s --prefix %s %s' "$PI_NPM_INSTALL_MIN_AGE_ARG" "$PI_NPM_INSTALL_PREFIX" "$PI_PACKAGE"
  else
    printf 'npm install -g --ignore-scripts %s %s' "$PI_NPM_INSTALL_MIN_AGE_ARG" "$PI_PACKAGE"
  fi
}

pi_locked_install_enabled() {
  case "${PI_EXPERIMENTAL:-}" in
    1|true|TRUE|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

install_pi_package() {
  if [ -t 1 ] && [ "${TERM:-}" != "dumb" ]; then
    install_pi_package_with_progress
  else
    printf 'Installing Pi...\n\n'
    run_pi_install error
  fi
}

run_pi_install() {
  npm_loglevel="$1"
  if pi_locked_install_enabled; then
    run_locked_install_pi "$npm_loglevel"
  else
    run_npm_install_pi "$npm_loglevel"
  fi
}

run_npm_install_pi() {
  npm_loglevel="$1"
  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ]; then
    npm install -g --ignore-scripts "$PI_NPM_INSTALL_MIN_AGE_ARG" --prefix "$PI_NPM_INSTALL_PREFIX" --no-fund --no-audit "--loglevel=$npm_loglevel" --progress=false "$PI_PACKAGE"
  else
    npm install -g --ignore-scripts "$PI_NPM_INSTALL_MIN_AGE_ARG" --no-fund --no-audit "--loglevel=$npm_loglevel" --progress=false "$PI_PACKAGE"
  fi
}

pi_effective_npm_install_prefix() {
  if [ -n "${PI_NPM_INSTALL_PREFIX:-}" ]; then
    printf '%s' "$PI_NPM_INSTALL_PREFIX"
  else
    npm_global_prefix
  fi
}

download_installer_artifact() {
  url="$1"
  output="$2"
  label="$3"

  if ! command -v curl >/dev/null 2>&1; then
    printf 'curl is not available for the locked installer.\n' >&2
    return 2
  fi

  http_status=$(curl -L -sS -w '%{http_code}' -o "$output" "$url") || {
    rm -f "$output"
    printf 'Could not download %s from %s.\n' "$label" "$url" >&2
    return 2
  }

  if [ "$http_status" = 200 ]; then
    return 0
  fi

  rm -f "$output"
  printf 'Locked installer %s is unavailable at %s (HTTP %s).\n' "$label" "$url" "$http_status" >&2
  return 2
}

locked_install_release_version() {
  metadata_file="$1"

  printf 'Resolving locked Pi release metadata\n' >&2
  download_installer_artifact "$PI_INSTALLER_API_BASE/latest" "$metadata_file" "latest metadata" || return 2

  node - "$metadata_file" <<'NODE'
const fs = require("node:fs");
const metadata = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const candidates = [
	metadata.version,
	metadata.tag,
	metadata.tagName,
	metadata.tag_name,
	metadata.release?.version,
	metadata.release?.tag,
	metadata.release?.tagName,
	metadata.release?.tag_name,
	metadata.latest?.version,
	metadata.latest?.tag,
	metadata.latest?.tagName,
	metadata.latest?.tag_name,
];
let version = candidates.find((value) => typeof value === "string" && value.length > 0);
if (version?.startsWith("v")) version = version.slice(1);
if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/.test(version ?? "")) {
	process.exit(1);
}
console.log(version);
NODE
}

download_locked_install_artifacts() {
  locked_tmp_dir="$1"

  if ! locked_version=$(locked_install_release_version "$locked_tmp_dir/metadata.json"); then
    printf 'Locked installer metadata is unavailable; falling back to npm install.\n' >&2
    return 2
  fi

  printf 'Downloading locked installer package.json for Pi %s\n' "$locked_version" >&2
  if ! download_installer_artifact "$PI_INSTALLER_API_BASE/$locked_version/package.json" "$locked_tmp_dir/package.json" "package.json"; then
    printf 'Locked installer package.json is unavailable for Pi %s; falling back to npm install.\n' "$locked_version" >&2
    return 2
  fi

  printf 'Downloading locked installer package-lock.json for Pi %s\n' "$locked_version" >&2
  if ! download_installer_artifact "$PI_INSTALLER_API_BASE/$locked_version/package-lock.json" "$locked_tmp_dir/package-lock.json" "package-lock.json"; then
    printf 'Locked installer package-lock.json is unavailable for Pi %s; falling back to npm install.\n' "$locked_version" >&2
    return 2
  fi

  validate_locked_install_artifacts "$locked_tmp_dir/package.json" "$locked_tmp_dir/package-lock.json" "$locked_version"
}

validate_locked_install_artifacts() {
  package_json_path="$1"
  package_lock_path="$2"
  locked_version="$3"

  node - "$package_json_path" "$package_lock_path" "$PI_PACKAGE" "$locked_version" <<'NODE'
const fs = require("node:fs");
const packageJson = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const packageLock = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const piPackage = process.argv[4];
const version = process.argv[5];

if (packageJson.dependencies?.[piPackage] !== version) {
	throw new Error(`installer package.json must depend on ${piPackage}@${version}`);
}
if (packageLock.lockfileVersion !== 3) {
	throw new Error("installer package-lock.json must use lockfileVersion 3");
}
if (packageLock.packages?.[""]?.dependencies?.[piPackage] !== version) {
	throw new Error(`installer package-lock.json root must depend on ${piPackage}@${version}`);
}
if (!packageLock.packages?.[`node_modules/${piPackage}`]) {
	throw new Error(`installer package-lock.json does not include node_modules/${piPackage}`);
}
NODE
}

install_locked_node_modules_tree() {
  locked_tmp_dir="$1"
  install_prefix="$2"

  node - "$locked_tmp_dir" "$install_prefix" "$PI_PACKAGE" "$PI_CMD" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const stagingDir = process.argv[2];
const installPrefix = process.argv[3];
const packageName = process.argv[4];
const commandName = process.argv[5];

const packageParts = packageName.split("/");
const rootNodeModules = path.join(stagingDir, "node_modules");
const stagedPackageDir = path.join(rootNodeModules, ...packageParts);
const nestedNodeModules = path.join(stagedPackageDir, "node_modules");
const packageJson = JSON.parse(fs.readFileSync(path.join(stagedPackageDir, "package.json"), "utf8"));
const binPath = typeof packageJson.bin === "string" ? packageJson.bin : packageJson.bin?.[commandName];

if (!fs.statSync(stagedPackageDir).isDirectory()) {
	throw new Error(`${packageName} was not installed by npm ci`);
}
if (!binPath) {
	throw new Error(`${packageName} does not declare a ${commandName} bin`);
}

fs.mkdirSync(nestedNodeModules, { recursive: true });

for (const entryName of fs.readdirSync(rootNodeModules)) {
	if (entryName === ".package-lock.json") continue;
	const entryPath = path.join(rootNodeModules, entryName);

	if (entryName.startsWith("@")) {
		for (const scopedName of fs.readdirSync(entryPath)) {
			const scopedPackageName = `${entryName}/${scopedName}`;
			if (scopedPackageName === packageName) continue;
			const destScope = path.join(nestedNodeModules, entryName);
			fs.mkdirSync(destScope, { recursive: true });
			fs.renameSync(path.join(entryPath, scopedName), path.join(destScope, scopedName));
		}
		continue;
	}

	fs.renameSync(entryPath, path.join(nestedNodeModules, entryName));
}

const targetNodeModules = path.join(installPrefix, "lib", "node_modules");
const targetPackageDir = path.join(targetNodeModules, ...packageParts);
const targetBinDir = path.join(installPrefix, "bin");
const targetCli = path.join(targetPackageDir, binPath);
const targetBin = path.join(targetBinDir, commandName);

fs.rmSync(targetPackageDir, { recursive: true, force: true });
fs.mkdirSync(path.dirname(targetPackageDir), { recursive: true });
fs.cpSync(stagedPackageDir, targetPackageDir, { recursive: true, verbatimSymlinks: true });
fs.chmodSync(targetCli, 0o755);

fs.mkdirSync(targetBinDir, { recursive: true });
fs.rmSync(targetBin, { force: true });
fs.symlinkSync(path.relative(targetBinDir, targetCli), targetBin);
NODE
}

run_locked_install_pi() {
  npm_loglevel="$1"
  locked_tmp_dir="${TMPDIR:-/tmp}/pi-installer-lock.$$"

  rm -rf "$locked_tmp_dir"
  mkdir -p "$locked_tmp_dir"

  if download_locked_install_artifacts "$locked_tmp_dir"; then
    locked_artifacts_status=0
  else
    locked_artifacts_status=$?
  fi

  if [ "$locked_artifacts_status" -ne 0 ]; then
    rm -rf "$locked_tmp_dir"
    if [ "$locked_artifacts_status" -eq 2 ]; then
      run_npm_install_pi "$npm_loglevel"
      return $?
    fi
    return "$locked_artifacts_status"
  fi

  install_prefix=$(pi_effective_npm_install_prefix)
  printf 'Installing locked Pi dependencies\n' >&2
  if (cd "$locked_tmp_dir" && npm ci --ignore-scripts "$PI_NPM_INSTALL_MIN_AGE_ARG" --omit=dev --include=optional --no-fund --no-audit "--loglevel=$npm_loglevel" --progress=false); then
    locked_install_status=0
  else
    locked_install_status=$?
  fi
  if [ "$locked_install_status" -ne 0 ]; then
    rm -rf "$locked_tmp_dir"
    return "$locked_install_status"
  fi

  printf 'Installing locked Pi into %s\n' "$install_prefix" >&2
  if install_locked_node_modules_tree "$locked_tmp_dir" "$install_prefix"; then
    locked_install_status=0
  else
    locked_install_status=$?
  fi
  if [ "$locked_install_status" -ne 0 ]; then
    rm -rf "$locked_tmp_dir"
    return "$locked_install_status"
  fi
  rm -rf "$locked_tmp_dir"
  printf 'Locked Pi install complete\n' >&2
}

uninstall_pi_package() {
  if ! npm_package_is_installed_for_uninstall; then
    printf 'I found pi at:\n\n  %s\n\n' "$PI_EXISTING_PATH" >&2
    printf 'but npm does not show %s installed there.\n' "$PI_PACKAGE" >&2
    printf 'Nothing was removed.\n' >&2
    return 1
  fi

  printf 'Uninstalling Pi...\n\n'
  run_npm_uninstall_pi error
  hash -r

  if [ -e "$PI_EXISTING_PATH" ] || [ -L "$PI_EXISTING_PATH" ]; then
    printf '\nnpm uninstall finished, but pi is still present at:\n\n  %s\n' "$PI_EXISTING_PATH" >&2
    return 1
  fi
}

npm_package_is_installed_for_uninstall() {
  if [ -n "${PI_NPM_UNINSTALL_PREFIX:-}" ]; then
    npm ls -g --prefix "$PI_NPM_UNINSTALL_PREFIX" --depth=0 "$PI_PACKAGE" >/dev/null 2>&1
  else
    npm ls -g --depth=0 "$PI_PACKAGE" >/dev/null 2>&1
  fi
}

run_npm_uninstall_pi() {
  npm_loglevel="$1"
  if [ -n "${PI_NPM_UNINSTALL_PREFIX:-}" ]; then
    npm uninstall -g --prefix "$PI_NPM_UNINSTALL_PREFIX" --no-fund --no-audit "--loglevel=$npm_loglevel" --progress=false "$PI_PACKAGE"
  else
    npm uninstall -g --no-fund --no-audit "--loglevel=$npm_loglevel" --progress=false "$PI_PACKAGE"
  fi
}

install_pi_package_with_progress() {
  log_file="${TMPDIR:-/tmp}/pi-installer-npm.$$"
  rm -f "$log_file"
  : >"$log_file"

  run_pi_install verbose >"$log_file" 2>&1 &
  npm_pid=$!

  printf '\033[?25l'
  animate_npm_install "$log_file" &
  progress_pid=$!
  trap 'kill "$npm_pid" 2>/dev/null || true; finish_install_progress "$progress_pid"; exit 130' INT TERM

  if wait "$npm_pid"; then
    status=0
  else
    status=$?
  fi

  finish_install_progress "$progress_pid"
  trap - INT TERM

  if [ "$status" -ne 0 ]; then
    printf '\033[31mInstallation failed.\033[0m\n\n'
    cat "$log_file"
    rm -f "$log_file"
    return "$status"
  fi

  rm -f "$log_file"
  if terminal_supports_unicode; then
    printf '  \033[32m✓\033[0m install complete\n'
  else
    printf '  \033[32mok\033[0m install complete\n'
  fi
}

finish_install_progress() {
  progress_pid="$1"

  kill "$progress_pid" 2>/dev/null || true
  wait "$progress_pid" 2>/dev/null || true
  printf '\r\033[K\033[?25h'
}

terminal_supports_unicode() {
  locale="${LC_ALL:-${LC_CTYPE:-${LANG:-}}}"

  case "$locale" in
    *UTF-8*|*utf-8*|*UTF8*|*utf8*) return 0 ;;
  esac

  case "${TERM_PROGRAM:-}" in
    Apple_Terminal|iTerm.app|vscode|WezTerm) return 0 ;;
  esac

  return 1
}

spinner_frame() {
  frame_step="$1"
  frame_count="$2"

  if [ "$frame_count" -eq 10 ]; then
    case $((frame_step % 10)) in
      0) printf '⠋' ;;
      1) printf '⠙' ;;
      2) printf '⠹' ;;
      3) printf '⠸' ;;
      4) printf '⠼' ;;
      5) printf '⠴' ;;
      6) printf '⠦' ;;
      7) printf '⠧' ;;
      8) printf '⠇' ;;
      *) printf '⠏' ;;
    esac
  else
    case $((frame_step % 4)) in
      0) printf '-' ;;
      1) printf '\\' ;;
      2) printf '|' ;;
      *) printf '/' ;;
    esac
  fi
}

animate_npm_install() {
  log_file="$1"

  if terminal_supports_unicode; then
    full="█"
    empty="░"
    frame_count=10
  else
    full="#"
    empty="-"
    frame_count=4
  fi

  step=0
  if pi_locked_install_enabled; then
    label="starting locked install"
  else
    label="starting npm install"
  fi
  while :; do
    frame=$(spinner_frame "$step" "$frame_count")
    if [ $((step % 5)) -eq 0 ]; then
      label=$(npm_install_progress_label "$log_file" "$label")
    fi
    draw_install_progress "$step" "$frame" "$label" "$full" "$empty"
    step=$((step + 1))
    sleep 0.08
  done
}

animate_node_install() {
  log_file="$1"
  method_label="$2"

  if terminal_supports_unicode; then
    full="█"
    empty="░"
    frame_count=10
  else
    full="#"
    empty="-"
    frame_count=4
  fi

  step=0
  label="starting ${method_label} install"
  while :; do
    frame=$(spinner_frame "$step" "$frame_count")
    if [ $((step % 5)) -eq 0 ]; then
      label=$(node_install_progress_label "$log_file" "$label")
    fi
    draw_install_progress "$step" "$frame" "$label" "$full" "$empty" "Installing Node.js"
    step=$((step + 1))
    sleep 0.08
  done
}

node_install_progress_label() {
  log_file="$1"
  label="$2"

  while IFS= read -r line; do
    line=${line##*"$PI_CR"}
    case "$line" in
      "") ;;
      Resolving\ Node.js*) label="resolving Node.js binary" ;;
      Downloading\ Node.js*) label="$line" ;;
      Verifying\ Node.js*) label="verifying download" ;;
      Installing\ xz-utils*) label="installing xz-utils" ;;
      Extracting\ Node.js*) label="extracting Node.js" ;;
      Node.js\ installed*) label="Node.js installed" ;;
      Hit:*|Get:*|Ign:*) label="updating package lists" ;;
      Reading\ package\ lists*) label="reading package lists" ;;
      Building\ dependency\ tree*) label="resolving dependencies" ;;
      The\ following\ NEW\ packages*) label="installing dependencies" ;;
      Need\ to\ get*|Fetched\ *) label="$line" ;;
      Selecting\ previously\ unselected\ package*) label="selecting packages" ;;
      Preparing\ to\ unpack*) label="preparing packages" ;;
      Unpacking\ *|Setting\ up\ *) label="$line" ;;
      fetch\ *) label="fetching packages" ;;
      *Installing\ nodejs*) label="$line" ;;
      OK:\ *) label="$line" ;;
      ==\>\ Downloading*) label="downloading packages" ;;
      ==\>\ Installing*|==\>\ Upgrading*) label="$line" ;;
      ==\>\ Pouring*) label="installing package" ;;
      *already\ installed*) label="$line" ;;
    esac
  done < "$log_file"

  if [ "${#label}" -gt 64 ]; then
    label=$(printf '%.61s...' "$label")
  fi
  printf '%s' "$label"
}

npm_install_progress_label() {
  log_file="$1"
  label="$2"
  metadata_cache_count=0
  metadata_fetch_count=0
  tarball_cache_count=0
  tarball_fetch_count=0

  while IFS= read -r line; do
    line=${line%"$PI_CR"}
    case "$line" in
      Resolving\ locked\ Pi\ release*)
        label="resolving locked release"
        ;;
      Downloading\ locked\ installer\ package.json*)
        label="fetching locked package manifest"
        ;;
      Downloading\ locked\ installer\ package-lock.json*)
        label="fetching locked package lock"
        ;;
      Locked\ installer\ *falling\ back*)
        label="falling back to npm install"
        ;;
      Installing\ locked\ Pi\ dependencies*)
        label="installing locked dependencies"
        ;;
      Installing\ locked\ Pi\ into*)
        label="installing locked package"
        ;;
      Locked\ Pi\ install\ complete*)
        label="locked install complete"
        ;;
      npm\ verbose\ title\ npm\ install*)
        label="resolving packages"
        ;;
      npm\ http\ fetch\ GET\ *https://registry.npmjs.org/*.tgz*)
        tarball_fetch_count=$((tarball_fetch_count + 1))
        label="fetching tarballs (${tarball_fetch_count})"
        ;;
      npm\ http\ cache\ *@https://registry.npmjs.org/*.tgz*)
        tarball_cache_count=$((tarball_cache_count + 1))
        if [ "$tarball_fetch_count" -gt 0 ]; then
          label="fetching tarballs (${tarball_fetch_count})"
        else
          label="checking tarballs (${tarball_cache_count})"
        fi
        ;;
      npm\ http\ fetch\ GET\ *https://registry.npmjs.org/*)
        metadata_fetch_count=$((metadata_fetch_count + 1))
        label="fetching package metadata (${metadata_fetch_count})"
        ;;
      npm\ http\ cache\ https://registry.npmjs.org/*)
        metadata_cache_count=$((metadata_cache_count + 1))
        if [ "$metadata_fetch_count" -gt 0 ]; then
          label="fetching package metadata (${metadata_fetch_count})"
        else
          label="checking cached metadata (${metadata_cache_count})"
        fi
        ;;
      npm\ info\ run\ *)
        rest=${line#npm info run }
        package=${rest%% *}
        rest=${rest#* }
        script=${rest%% *}
        package=${package%@*}
        case "$line" in
          *\{\ code:*) label="finished ${script} for ${package}" ;;
          *) label="running ${script} for ${package}" ;;
        esac
        ;;
      changed\ *|added\ *|removed\ *|updated\ *|up\ to\ date\ *)
        label="$line"
        ;;
    esac
  done < "$log_file"

  printf '%s' "$label"
}

draw_install_progress() {
  step="$1"; frame="$2"; label="$3"; full="$4"; empty="$5"; title="${6:-Installing Pi}"

  reset="${PI_ESC}[0m"
  dim="${PI_ESC}[2m"
  cyan="${PI_ESC}[36m"
  red="${PI_ESC}[31m"
  green="${PI_ESC}[32m"
  orange="${PI_ESC}[33m"
  bold="${PI_ESC}[1m"

  width=28
  trail=8
  head=$((step % (width + trail)))
  bar=""

  i=0
  while [ "$i" -lt "$width" ]; do
    age=$((head - i))
    if [ "$age" -ge 0 ] && [ "$age" -lt "$trail" ]; then
      case "$age" in
        0|1) cell="${green}${full}${reset}" ;;
        2|3) cell="${cyan}${full}${reset}" ;;
        4|5) cell="${red}${full}${reset}" ;;
        *) cell="${orange}${full}${reset}" ;;
      esac
    else
      cell="${dim}${empty}${reset}"
    fi
    bar="${bar}${cell}"
    i=$((i + 1))
  done

  printf '\r\033[K  %s%s%s %s %s%s%s %s' "$orange" "$frame" "$reset" "$bar" "$bold" "$title" "$reset" "$label"
}

pi_logo_animation() {
  if [ ! -t 1 ] || [ "${TERM:-}" = "dumb" ]; then
    print_static_logo
    return
  fi

  esc="${PI_ESC}["
  reset="${PI_ESC}[0m"
  hide="${esc}?25l"
  show="${esc}?25h"
  clear="${esc}H"

  printf '%s%s' "$hide" "${esc}2J${esc}H"

  for y in 0 1 2 3; do draw_logo_frame "$clear" "$reset" 0 left 2 "$y" 0 0; sleep 0.075; done
  for y in 0 1 2; do draw_logo_frame "$clear" "$reset" 1 top 2 "$y" 0 0; sleep 0.075; done
  for y in 0 1 2 3 4; do draw_logo_frame "$clear" "$reset" 2 right 5 "$y" 0 0; sleep 0.075; done

  draw_logo_frame "$clear" "$reset" 3 none 0 0 0 0; sleep 0.25
  draw_logo_frame "$clear" "$reset" 3 none 0 0 1 0; sleep 0.08
  draw_logo_frame "$clear" "$reset" 3 none 0 0 0 0; sleep 0.08
  draw_logo_frame "$clear" "$reset" 3 none 0 0 1 0; sleep 0.08
  draw_logo_frame "$clear" "$reset" 4 none 0 0 0 0; sleep 0.10
  draw_logo_frame "$clear" "$reset" 5 none 0 0 0 0; sleep 0.45
  draw_logo_frame "$clear" "$reset" 5 none 0 0 0 1; sleep 0.12
  draw_logo_frame "$clear" "$reset" 5 none 0 0 0 0; sleep 0.12
  draw_logo_frame "$clear" "$reset" 5 none 0 0 0 1; sleep 0.45

  printf '%s%s\n' "$reset" "$show"
}

draw_logo_frame() {
  clear="$1"; reset="$2"; phase="$3"; active="$4"; ax="$5"; ay="$6"; flash="$7"; white="$8"

  left=0
  top=0

  panel_cell="${reset}  "
  cyan_cell="${PI_ESC}[36m██"
  red_cell="${PI_ESC}[31m██"
  green_cell="${PI_ESC}[32m██"
  orange_cell="${PI_ESC}[33m██"
  white_cell="${PI_ESC}[39m██"
  flash_cell="${PI_ESC}[33m██"

  pad=$(repeat_space "$left")
  clear_cell="$panel_cell"
  frame="$clear"
  i=0
  while [ "$i" -lt "$top" ]; do frame="${frame}\n"; i=$((i + 1)); done

  for y in 0 1 2 3 4 5 6 7 8; do
    frame="${frame}${pad}"
    for x in 1 2 3 4 5 6 7 8; do
      set_logo_cell_color "$phase" "$active" "$ax" "$ay" "$flash" "$white" "$y" "$x"
      case "$LOGO_COLOR" in
        cyan) cell="$cyan_cell" ;;
        red) cell="$red_cell" ;;
        green) cell="$green_cell" ;;
        orange) cell="$orange_cell" ;;
        white) cell="$white_cell" ;;
        flash) cell="$flash_cell" ;;
        *) cell="$clear_cell" ;;
      esac
      frame="${frame}${cell}"
    done
    frame="${frame}${reset}\n"
  done
  printf '%b' "$frame"
}

set_logo_cell_color() {
  phase="$1"; active="$2"; ax="$3"; ay="$4"; flash="$5"; white="$6"; y="$7"; x="$8"

  if [ "$white" = 1 ]; then
    if in_cells "$y" "$x" "3,2 3,3 3,4 4,2 4,4 5,2 5,3 5,5 6,2 6,5"; then LOGO_COLOR=white; else LOGO_COLOR=panel; fi
    return
  fi
  if [ "$flash" = 1 ] && [ "$y" = 6 ] && [ "$x" -ge 1 ] && [ "$x" -le 6 ]; then LOGO_COLOR=flash; return; fi

  case "$active" in
    left)  if in_piece "$y" "$x" "$ay" "$ax" "0,0 1,0 1,1 2,0"; then LOGO_COLOR=red; return; fi ;;
    top)   if in_piece "$y" "$x" "$ay" "$ax" "0,0 0,1 0,2 1,2"; then LOGO_COLOR=cyan; return; fi ;;
    right) if in_piece "$y" "$x" "$ay" "$ax" "0,0 1,0 2,0 2,1"; then LOGO_COLOR=green; return; fi ;;
  esac

  if [ "$phase" = 4 ]; then
    if in_cells "$y" "$x" "2,2 2,3 2,4 3,4"; then LOGO_COLOR=cyan; return; fi
    if in_cells "$y" "$x" "3,2 4,2 4,3 5,2"; then LOGO_COLOR=red; return; fi
    if in_cells "$y" "$x" "4,5 5,5"; then LOGO_COLOR=green; return; fi
    LOGO_COLOR=panel; return
  fi

  if [ "$phase" -ge 5 ]; then
    if in_cells "$y" "$x" "3,2 3,3 3,4 4,4"; then LOGO_COLOR=cyan; return; fi
    if in_cells "$y" "$x" "4,2 5,2 5,3 6,2"; then LOGO_COLOR=red; return; fi
    if in_cells "$y" "$x" "5,5 6,5"; then LOGO_COLOR=green; return; fi
    LOGO_COLOR=panel; return
  fi

  if [ "$phase" -le 3 ] && in_cells "$y" "$x" "6,1 6,2 6,3 6,4"; then LOGO_COLOR=orange; return; fi
  if [ "$phase" -ge 2 ] && in_cells "$y" "$x" "2,2 2,3 2,4 3,4"; then LOGO_COLOR=cyan; return; fi
  if [ "$phase" -ge 1 ] && in_cells "$y" "$x" "3,2 4,2 4,3 5,2"; then LOGO_COLOR=red; return; fi
  if [ "$phase" -ge 3 ] && in_cells "$y" "$x" "4,5 5,5 6,5 6,6"; then LOGO_COLOR=green; return; fi

  LOGO_COLOR=panel
}

in_piece() {
  y="$1"; x="$2"; py="$3"; px="$4"; cells="$5"
  for item in $cells; do
    dy=${item%,*}; dx=${item#*,}
    [ "$y" -eq $((py + dy)) ] && [ "$x" -eq $((px + dx)) ] && return 0
  done
  return 1
}

in_cells() {
  y="$1"; x="$2"; shift 2
  for item in $1; do
    [ "$item" = "$y,$x" ] && return 0
  done
  return 1
}

repeat_space() {
  count="$1"; out=""
  while [ "$count" -gt 0 ]; do out=" $out"; count=$((count - 1)); done
  printf '%s' "$out"
}

print_static_logo() {
  cat <<'EOF'

  ██████
  ██  ██
  ████  ██
  ██    ██

EOF
}

pi_installer_main "$@"
