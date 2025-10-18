#!/bin/bash

# Функция, которая будет генерировать варианты автодополнения.
# Имя _add_new_lecture_completion - это соглашение: _имя_скрипта_completion
_add_new_lecture_completion() {
    # COMP_WORDS: массив слов в текущей командной строке.
    # COMP_CWORD: индекс слова, на котором сейчас находится курсор.
    # cur: текущее слово, которое мы пытаемся дополнить.
    # prev: слово перед текущим.
    local cur prev opts
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Список всех возможных флагов для нашего скрипта
    opts="-s --subject-id -t --lecture-type -r --classroom -i --absolute-lecture-id --relative-lecture-id -d --date -o --open --help"

    # Основная логика: смотрим на слово перед курсором (`prev`)
    # и решаем, что подставлять.
    case "${prev}" in
        -s|--subject-id)
            # Если предыдущий флаг -s, читаем ID из subjects.json с помощью jq
            # Убедитесь, что jq установлен! (sudo apt install jq / brew install jq)
            local subjects
            if [ -f "subjects.json" ]; then
                subjects=$(jq -r 'keys[]' subjects.json)
                COMPREPLY=( $(compgen -W "${subjects}" -- "${cur}") )
            fi
            return 0
            ;;
        -t|--lecture-type)
            # Если предыдущий флаг -t, предлагаем "л" или "пр"
            COMPREPLY=( $(compgen -W "л пр" -- "${cur}") )
            return 0
            ;;
        # Для этих флагов аргумент - это число или строка,
        # автодополнение не имеет смысла, поэтому мы ничего не делаем.
        -r|--classroom|-i|--absolute-lecture-id|--relative-lecture-id|-d|--date)
            COMPREPLY=()
            return 0
            ;;
    esac

    # Если мы не попали ни в одно из условий выше,
    # значит, мы дополняем сам флаг.
    COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
}

# Регистрируем нашу функцию `_add_new_lecture_completion`
# для команды `add_new_lecture.py`.
complete -F _add_new_lecture_completion add_new_lecture.py
