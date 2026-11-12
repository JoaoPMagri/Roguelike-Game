import json
import os
import sys
from typing import Optional


def get_resource_path(relative_path: str) -> str:
    """
    Retorna o caminho absoluto para recursos de leitura (assets).
    Funciona tanto em execução direta (.py) quanto empacotado em executável
    (PyInstaller --onefile / --onedir via sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def get_save_dir() -> str:
    """
    Retorna um diretório persistente para salvar dados locais.
    - Quando executado como .exe (frozen), prioriza uma pasta 'saves' ao lado do
      executável (fora do diretório temporário _MEIPASS). Caso o diretório do
      executável não tenha permissão de escrita (ex.: Program Files), utiliza
      automaticamente o diretório de dados do usuário (%LOCALAPPDATA%).
    - Em modo de desenvolvimento (.py), utiliza a pasta 'saves' na raiz do projeto.
    """
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(exe_dir, "saves")
        try:
            os.makedirs(candidate, exist_ok=True)
            test_file = os.path.join(candidate, ".write_test")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(test_file)
            return candidate
        except OSError:
            appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            fallback = os.path.join(appdata, "RoguelikeProcedural", "saves")
            os.makedirs(fallback, exist_ok=True)
            return fallback

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    save_dir = os.path.join(project_root, "saves")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def get_save_file_path() -> str:
    return os.path.join(get_save_dir(), "savegame.json")


def get_settings_file_path() -> str:
    return os.path.join(get_save_dir(), "settings.json")


class SaveManager:
    SAVE_VERSION = 1

    @staticmethod
    def has_save() -> bool:
        path = get_save_file_path()
        return os.path.isfile(path)

    @staticmethod
    def save_game(
        selected_character: dict,
        player,
        master_seed: float,
        available_map_types: list,
        levels_history: list,
        current_level_idx: int,
        explored_tiles_by_level: dict = None,
        extra_data: dict = None,
    ) -> bool:
        """
        Salva o estado completo da partida em JSON de forma atômica.
        Estruturado para suportar futuramente inimigos, combate e inventário.
        """
        if selected_character is None or not levels_history or current_level_idx < 0:
            return False

        serialized_explored = {}
        if explored_tiles_by_level:
            for lvl_idx, coords in explored_tiles_by_level.items():
                serialized_explored[str(lvl_idx)] = [
                    [int(x), int(y)] for x, y in coords
                ]

        extra = extra_data or {}

        payload = {
            "version": SaveManager.SAVE_VERSION,
            "character": selected_character,
            "player": {
                "x": float(player.x),
                "y": float(player.y),
                "direction": getattr(player, "direction", "down"),
                # Campos reservados para futuras expansões de combate e itens
                "stats": extra.get("player_stats", {}),
                "combat": extra.get("player_combat", {}),
                "inventory": extra.get("inventory", []),
            },
            "world": {
                "master_seed": master_seed,
                "available_map_types": list(available_map_types),
                "current_level_idx": int(current_level_idx),
                "levels_history": levels_history,
                "explored_tiles_by_level": serialized_explored,
                # Campos reservados para futuras expansões de entidades por nível
                "enemies_by_level": extra.get("enemies_by_level", {}),
                "items_by_level": extra.get("items_by_level", {}),
            },
        }

        save_path = get_save_file_path()
        temp_path = save_path + ".tmp"

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, save_path)
            return True
        except OSError as exc:
            print(f"Erro ao salvar partida: {exc}")
            return False

    @staticmethod
    def load_game() -> Optional[dict]:
        """Carrega os dados salvos localmente ou retorna None se não existir/inválido."""
        save_path = get_save_file_path()
        if not os.path.isfile(save_path):
            return None

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "world" not in data or "player" not in data:
                return None
            return data
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Erro ao carregar save: {exc}")
            return None

    @staticmethod
    def save_settings(width: int, height: int, fps: int) -> bool:
        """Salva localmente as configurações de janela e FPS."""
        settings_path = get_settings_file_path()
        temp_path = settings_path + ".tmp"
        payload = {
            "width": int(width),
            "height": int(height),
            "fps": int(fps),
        }
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(temp_path, settings_path)
            return True
        except OSError as exc:
            print(f"Erro ao salvar configurações: {exc}")
            return False

    @staticmethod
    def load_settings(default_width: int, default_height: int, default_fps: int) -> dict:
        """Carrega as configurações salvas ou retorna os valores padrão."""
        settings_path = get_settings_file_path()
        if not os.path.isfile(settings_path):
            return {
                "width": default_width,
                "height": default_height,
                "fps": default_fps,
            }
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "width": int(data.get("width", default_width)),
                "height": int(data.get("height", default_height)),
                "fps": int(data.get("fps", default_fps)),
            }
        except (OSError, ValueError, json.JSONDecodeError):
            return {
                "width": default_width,
                "height": default_height,
                "fps": default_fps,
            }

