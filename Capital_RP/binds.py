from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import keyboard
    import pydirectinput
except ImportError as exc:
    raise SystemExit(
        "Dependencias ausentes. Instale com: pip install keyboard pydirectinput"
    ) from exc


APP_TITLE = "Painel de Binds - FiveM"
APP_VERSION = "1.1.0"

DATA_FILE = Path(__file__).with_name("binds_fivem.json")
AUTOMATION_FILE = Path(__file__).with_name("automacao_fivem.json")

CONSOLE_KEY = "f8"

DEFAULT_EXECUTION_DELAY = 2.5
TYPE_INTERVAL = 0.008
CONSOLE_OPEN_DELAY = 0.45
COMMAND_DELAY = 0.22
AUTOMATION_LOOP_INTERVAL = 0.10

# Evita que a automacao de comer/beber envie uma tecla enquanto o console F8
# estiver sendo utilizado para criar ou remover uma bind.
INPUT_LOCK = threading.Lock()

pydirectinput.PAUSE = 0.05


@dataclass(slots=True)
class BindItem:
    name: str
    key: str
    command: str


@dataclass(slots=True)
class AutomationConfig:
    eat_enabled: bool = True
    eat_key: str = "4"
    eat_minutes: float = 5.0
    drink_enabled: bool = True
    drink_key: str = "5"
    drink_minutes: float = 3.0


class BindRepository:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def load(self) -> list[BindItem]:
        if not self.file_path.exists():
            return []

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        items: list[BindItem] = []

        if not isinstance(raw, list):
            return items

        for entry in raw:
            if not isinstance(entry, dict):
                continue

            name = str(entry.get("name", "")).strip()
            key = str(entry.get("key", "")).strip().upper()
            command = str(entry.get("command", "")).strip()

            if key and command:
                items.append(BindItem(name=name, key=key, command=command))

        return items

    def save(self, items: list[BindItem]) -> None:
        payload = [asdict(item) for item in items]

        self.file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class AutomationRepository:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def load(self) -> AutomationConfig:
        if not self.file_path.exists():
            return AutomationConfig()

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AutomationConfig()

        if not isinstance(raw, dict):
            return AutomationConfig()

        try:
            return AutomationConfig(
                eat_enabled=bool(raw.get("eat_enabled", True)),
                eat_key=str(raw.get("eat_key", "4")).strip().upper() or "4",
                eat_minutes=float(raw.get("eat_minutes", 5.0)),
                drink_enabled=bool(raw.get("drink_enabled", True)),
                drink_key=str(raw.get("drink_key", "5")).strip().upper() or "5",
                drink_minutes=float(raw.get("drink_minutes", 3.0)),
            )
        except (TypeError, ValueError):
            return AutomationConfig()

    def save(self, config: AutomationConfig) -> None:
        self.file_path.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class FiveMBindService:
    @staticmethod
    def normalize_key(value: str) -> str:
        return value.strip().upper()

    @staticmethod
    def validate_key(value: str) -> str:
        key = FiveMBindService.normalize_key(value)

        if not key:
            raise ValueError("Informe a tecla da bind.")

        if key == "F8":
            raise ValueError("F8 esta reservada para abrir o console do FiveM.")

        if any(char in key for char in ('"', "'", ";", " ")):
            raise ValueError("A tecla informada contem caracteres invalidos.")

        return key

    @staticmethod
    def validate_command(value: str) -> str:
        command = value.strip()

        if not command:
            raise ValueError("Informe pelo menos um comando para a bind.")

        if '"' in command:
            raise ValueError("O comando nao pode conter aspas duplas.")

        if "\n" in command or "\r" in command:
            raise ValueError(
                "Use ';' para separar comandos, em vez de quebra de linha."
            )

        return command

    @classmethod
    def build_unbind_command(cls, key: str) -> str:
        clean_key = cls.validate_key(key)
        return f'unbind "{clean_key}"'

    @classmethod
    def build_bind_command(cls, key: str, command: str) -> str:
        clean_key = cls.validate_key(key)
        clean_command = cls.validate_command(command)
        return f'bind keyboard "{clean_key}" "{clean_command}"'

    @staticmethod
    def _type_console_command(command: str) -> None:
        keyboard.write(command, delay=TYPE_INTERVAL)
        pydirectinput.press("enter")
        time.sleep(COMMAND_DELAY)

    @classmethod
    def execute_apply(cls, key: str, command: str, start_delay: float) -> None:
        unbind_command = cls.build_unbind_command(key)
        bind_command = cls.build_bind_command(key, command)

        time.sleep(start_delay)

        with INPUT_LOCK:
            pydirectinput.press(CONSOLE_KEY)
            time.sleep(CONSOLE_OPEN_DELAY)

            cls._type_console_command(unbind_command)
            cls._type_console_command(bind_command)

            pydirectinput.press(CONSOLE_KEY)

    @classmethod
    def execute_unbind(cls, key: str, start_delay: float) -> None:
        unbind_command = cls.build_unbind_command(key)

        time.sleep(start_delay)

        with INPUT_LOCK:
            pydirectinput.press(CONSOLE_KEY)
            time.sleep(CONSOLE_OPEN_DELAY)

            cls._type_console_command(unbind_command)

            pydirectinput.press(CONSOLE_KEY)


class PeriodicKeyAutomation:
    def __init__(self) -> None:
        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        self._active = False
        self._config = AutomationConfig()
        self._eat_next: float | None = None
        self._drink_next: float | None = None
        self._last_action = ""
        self._last_action_at = ""

    @staticmethod
    def validate_minutes(value: float, label: str) -> float:
        try:
            minutes = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Informe um intervalo valido para {label}.") from exc

        if not math.isfinite(minutes) or minutes <= 0:
            raise ValueError(f"O intervalo de {label} deve ser maior que zero.")

        if minutes > 1440:
            raise ValueError(f"O intervalo de {label} deve ser de ate 1440 minutos.")

        return minutes

    @classmethod
    def validate_config(cls, config: AutomationConfig) -> AutomationConfig:
        if not config.eat_enabled and not config.drink_enabled:
            raise ValueError("Ative Comer, Beber ou os dois antes de iniciar.")

        eat_key = config.eat_key.strip().upper()
        drink_key = config.drink_key.strip().upper()
        eat_minutes = config.eat_minutes
        drink_minutes = config.drink_minutes

        if config.eat_enabled:
            eat_key = FiveMBindService.validate_key(eat_key)
            eat_minutes = cls.validate_minutes(eat_minutes, "Comer")

        if config.drink_enabled:
            drink_key = FiveMBindService.validate_key(drink_key)
            drink_minutes = cls.validate_minutes(drink_minutes, "Beber")

        return AutomationConfig(
            eat_enabled=config.eat_enabled,
            eat_key=eat_key,
            eat_minutes=float(eat_minutes),
            drink_enabled=config.drink_enabled,
            drink_key=drink_key,
            drink_minutes=float(drink_minutes),
        )

    def start(self, config: AutomationConfig) -> None:
        clean_config = self.validate_config(config)

        self.stop()

        now = time.monotonic()

        with self._state_lock:
            self._config = clean_config
            self._stop_event = threading.Event()
            self._active = True
            self._last_action = ""
            self._last_action_at = ""

            self._eat_next = (
                now + clean_config.eat_minutes * 60.0
                if clean_config.eat_enabled
                else None
            )
            self._drink_next = (
                now + clean_config.drink_minutes * 60.0
                if clean_config.drink_enabled
                else None
            )

            current_stop_event = self._stop_event
            self._thread = threading.Thread(
                target=self._run,
                args=(current_stop_event,),
                name="FiveMPeriodicKeyAutomation",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        with self._state_lock:
            thread = self._thread
            stop_event = self._stop_event
            self._active = False
            self._eat_next = None
            self._drink_next = None
            self._thread = None
            stop_event.set()

        if thread is not None and thread.is_alive():
            thread.join(timeout=0.5)

    def _run(self, stop_event: threading.Event) -> None:
        while not stop_event.wait(AUTOMATION_LOOP_INTERVAL):
            due_actions: list[tuple[str, str]] = []
            now = time.monotonic()

            with self._state_lock:
                if not self._active:
                    return

                config = self._config

                if (
                    config.eat_enabled
                    and self._eat_next is not None
                    and now >= self._eat_next
                ):
                    due_actions.append(("COMER", config.eat_key))
                    self._eat_next = now + config.eat_minutes * 60.0

                if (
                    config.drink_enabled
                    and self._drink_next is not None
                    and now >= self._drink_next
                ):
                    due_actions.append(("BEBER", config.drink_key))
                    self._drink_next = now + config.drink_minutes * 60.0

            for action_name, key in due_actions:
                if stop_event.is_set():
                    return

                with INPUT_LOCK:
                    pydirectinput.press(key.lower())

                with self._state_lock:
                    self._last_action = f"{action_name} - tecla {key}"
                    self._last_action_at = datetime.now().strftime("%H:%M:%S")

    def snapshot(self) -> dict[str, object]:
        now = time.monotonic()

        with self._state_lock:
            eat_remaining = (
                max(0.0, self._eat_next - now)
                if self._eat_next is not None
                else None
            )
            drink_remaining = (
                max(0.0, self._drink_next - now)
                if self._drink_next is not None
                else None
            )

            return {
                "active": self._active,
                "eat_remaining": eat_remaining,
                "drink_remaining": drink_remaining,
                "last_action": self._last_action,
                "last_action_at": self._last_action_at,
            }


class BindPanel(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("960x820")
        self.minsize(860, 730)

        self.repository = BindRepository(DATA_FILE)
        self.items = self.repository.load()

        self.automation_repository = AutomationRepository(AUTOMATION_FILE)
        self.automation_config = self.automation_repository.load()
        self.periodic_automation = PeriodicKeyAutomation()

        self.is_executing = False

        self.name_var = tk.StringVar()
        self.key_var = tk.StringVar(value="6")
        self.delay_var = tk.DoubleVar(value=DEFAULT_EXECUTION_DELAY)
        self.preview_unbind_var = tk.StringVar()
        self.preview_bind_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto.")

        self.eat_enabled_var = tk.BooleanVar(value=self.automation_config.eat_enabled)
        self.eat_key_var = tk.StringVar(value=self.automation_config.eat_key)
        self.eat_minutes_var = tk.DoubleVar(value=self.automation_config.eat_minutes)
        self.eat_countdown_var = tk.StringVar(value="--:--")

        self.drink_enabled_var = tk.BooleanVar(
            value=self.automation_config.drink_enabled
        )
        self.drink_key_var = tk.StringVar(value=self.automation_config.drink_key)
        self.drink_minutes_var = tk.DoubleVar(
            value=self.automation_config.drink_minutes
        )
        self.drink_countdown_var = tk.StringVar(value="--:--")
        self.automation_status_var = tk.StringVar(value="Automacao parada.")

        self._configure_style()
        self._build_ui()
        self._refresh_preview()
        self._refresh_tree()
        self._refresh_automation_controls()
        self._update_automation_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _key_values() -> list[str]:
        values = [f"F{i}" for i in range(1, 13) if i != 8]
        values += [chr(code) for code in range(ord("A"), ord("Z") + 1)]
        values += [str(i) for i in range(10)]
        return values

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        available = style.theme_names()

        if "vista" in available:
            style.theme_use("vista")
        elif "clam" in available:
            style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 9))
        style.configure("Status.TLabel", font=("Segoe UI", 9, "bold"))
        style.configure("Countdown.TLabel", font=("Consolas", 11, "bold"))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Painel de Binds - FiveM",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text="Edite binds pelo F8 e automatize Comer / Beber por intervalo.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self._build_bind_editor(root)
        self._build_periodic_automation(root)
        self._build_saved_binds(root)
        self._build_footer(root)

    def _build_bind_editor(self, root: ttk.Frame) -> None:
        editor = ttk.LabelFrame(root, text="Editor de binds", padding=12)
        editor.grid(row=1, column=0, sticky="ew", pady=(14, 10))
        editor.columnconfigure(1, weight=1)

        ttk.Label(editor, text="Nome / descricao:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )

        name_entry = ttk.Entry(editor, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)

        ttk.Label(editor, text="Tecla:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )

        self.key_combo = ttk.Combobox(
            editor,
            textvariable=self.key_var,
            values=self._key_values(),
            width=12,
        )
        self.key_combo.grid(row=1, column=1, sticky="w", pady=4)
        self.key_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._refresh_preview(),
        )
        self.key_combo.bind(
            "<KeyRelease>",
            lambda _event: self._refresh_preview(),
        )

        ttk.Label(editor, text="Atraso antes de executar:").grid(
            row=1,
            column=2,
            sticky="e",
            padx=(18, 8),
            pady=4,
        )

        delay_spin = ttk.Spinbox(
            editor,
            from_=0.5,
            to=10.0,
            increment=0.5,
            textvariable=self.delay_var,
            width=7,
        )
        delay_spin.grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(editor, text="seg").grid(
            row=1,
            column=4,
            sticky="w",
            padx=(4, 0),
        )

        ttk.Label(editor, text="Comando(s):").grid(
            row=2,
            column=0,
            sticky="nw",
            padx=(0, 10),
            pady=(6, 4),
        )

        self.command_text = tk.Text(
            editor,
            height=3,
            wrap="word",
            font=("Consolas", 10),
            undo=True,
        )
        self.command_text.grid(
            row=2,
            column=1,
            columnspan=4,
            sticky="ew",
            pady=(6, 4),
        )
        self.command_text.insert("1.0", "e meditar4;e continencia2")
        self.command_text.bind(
            "<KeyRelease>",
            lambda _event: self._refresh_preview(),
        )

        ttk.Label(
            editor,
            text=(
                "Separe varios comandos com ponto e virgula. "
                "Ex.: e meditar4;e continencia2"
            ),
            style="Subtitle.TLabel",
        ).grid(
            row=3,
            column=1,
            columnspan=4,
            sticky="w",
            pady=(0, 8),
        )

        preview = ttk.LabelFrame(editor, text="Previa do console", padding=8)
        preview.grid(
            row=4,
            column=0,
            columnspan=5,
            sticky="ew",
            pady=(4, 8),
        )
        preview.columnconfigure(0, weight=1)

        ttk.Label(
            preview,
            textvariable=self.preview_unbind_var,
            font=("Consolas", 9),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            preview,
            textvariable=self.preview_bind_var,
            font=("Consolas", 9),
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        actions = ttk.Frame(editor)
        actions.grid(
            row=5,
            column=0,
            columnspan=5,
            sticky="ew",
            pady=(4, 0),
        )

        for index in range(5):
            actions.columnconfigure(index, weight=1)

        self.apply_button = ttk.Button(
            actions,
            text="Aplicar bind",
            command=self.apply_bind,
        )
        self.apply_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.unbind_button = ttk.Button(
            actions,
            text="Somente limpar",
            command=self.clear_bind,
        )
        self.unbind_button.grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Button(
            actions,
            text="Salvar na lista",
            command=self.save_current,
        ).grid(row=0, column=2, sticky="ew", padx=4)

        ttk.Button(
            actions,
            text="Novo",
            command=self.new_form,
        ).grid(row=0, column=3, sticky="ew", padx=4)

        ttk.Button(
            actions,
            text="Excluir salvo",
            command=self.delete_selected,
        ).grid(row=0, column=4, sticky="ew", padx=(4, 0))

    def _build_periodic_automation(self, root: ttk.Frame) -> None:
        automation = ttk.LabelFrame(
            root,
            text="Automacao periodica - Comer / Beber",
            padding=12,
        )
        automation.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        automation.columnconfigure(2, weight=1)

        ttk.Checkbutton(
            automation,
            text="Comer",
            variable=self.eat_enabled_var,
            command=self._refresh_automation_controls,
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)

        ttk.Label(automation, text="Tecla:").grid(
            row=0, column=1, sticky="e", padx=(0, 6), pady=4
        )

        self.eat_key_combo = ttk.Combobox(
            automation,
            textvariable=self.eat_key_var,
            values=self._key_values(),
            width=8,
        )
        self.eat_key_combo.grid(row=0, column=2, sticky="w", pady=4)

        ttk.Label(automation, text="A cada:").grid(
            row=0, column=3, sticky="e", padx=(18, 6), pady=4
        )

        self.eat_minutes_spin = ttk.Spinbox(
            automation,
            from_=0.1,
            to=1440.0,
            increment=0.5,
            textvariable=self.eat_minutes_var,
            width=8,
        )
        self.eat_minutes_spin.grid(row=0, column=4, sticky="w", pady=4)

        ttk.Label(automation, text="min").grid(
            row=0, column=5, sticky="w", padx=(4, 14), pady=4
        )

        ttk.Label(automation, text="Proximo:").grid(
            row=0, column=6, sticky="e", padx=(0, 6), pady=4
        )

        ttk.Label(
            automation,
            textvariable=self.eat_countdown_var,
            style="Countdown.TLabel",
            width=9,
        ).grid(row=0, column=7, sticky="w", pady=4)

        ttk.Checkbutton(
            automation,
            text="Beber",
            variable=self.drink_enabled_var,
            command=self._refresh_automation_controls,
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

        ttk.Label(automation, text="Tecla:").grid(
            row=1, column=1, sticky="e", padx=(0, 6), pady=4
        )

        self.drink_key_combo = ttk.Combobox(
            automation,
            textvariable=self.drink_key_var,
            values=self._key_values(),
            width=8,
        )
        self.drink_key_combo.grid(row=1, column=2, sticky="w", pady=4)

        ttk.Label(automation, text="A cada:").grid(
            row=1, column=3, sticky="e", padx=(18, 6), pady=4
        )

        self.drink_minutes_spin = ttk.Spinbox(
            automation,
            from_=0.1,
            to=1440.0,
            increment=0.5,
            textvariable=self.drink_minutes_var,
            width=8,
        )
        self.drink_minutes_spin.grid(row=1, column=4, sticky="w", pady=4)

        ttk.Label(automation, text="min").grid(
            row=1, column=5, sticky="w", padx=(4, 14), pady=4
        )

        ttk.Label(automation, text="Proximo:").grid(
            row=1, column=6, sticky="e", padx=(0, 6), pady=4
        )

        ttk.Label(
            automation,
            textvariable=self.drink_countdown_var,
            style="Countdown.TLabel",
            width=9,
        ).grid(row=1, column=7, sticky="w", pady=4)

        buttons = ttk.Frame(automation)
        buttons.grid(
            row=2,
            column=0,
            columnspan=8,
            sticky="ew",
            pady=(8, 0),
        )
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        buttons.columnconfigure(2, weight=3)

        self.start_automation_button = ttk.Button(
            buttons,
            text="Iniciar automacao",
            command=self.start_periodic_automation,
        )
        self.start_automation_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )

        self.stop_automation_button = ttk.Button(
            buttons,
            text="Parar automacao",
            command=self.stop_periodic_automation,
        )
        self.stop_automation_button.grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Label(
            buttons,
            textvariable=self.automation_status_var,
            style="Status.TLabel",
        ).grid(row=0, column=2, sticky="w", padx=(14, 0))

        ttk.Label(
            automation,
            text=(
                "As teclas sao enviadas para a janela ativa. "
                "Depois de iniciar, deixe o FiveM em primeiro plano."
            ),
            style="Subtitle.TLabel",
        ).grid(
            row=3,
            column=0,
            columnspan=8,
            sticky="w",
            pady=(7, 0),
        )

    def _build_saved_binds(self, root: ttk.Frame) -> None:
        saved = ttk.LabelFrame(root, text="Binds salvas", padding=10)
        saved.grid(row=3, column=0, sticky="nsew")
        saved.columnconfigure(0, weight=1)
        saved.rowconfigure(0, weight=1)

        columns = ("name", "key", "command")

        self.tree = ttk.Treeview(
            saved,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("name", text="Nome")
        self.tree.heading("key", text="Tecla")
        self.tree.heading("command", text="Comando(s)")

        self.tree.column("name", width=220, anchor="w")
        self.tree.column("key", width=80, anchor="center", stretch=False)
        self.tree.column("command", width=500, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.load_selected)

        scrollbar = ttk.Scrollbar(
            saved,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _build_footer(self, root: ttk.Frame) -> None:
        footer = ttk.Frame(root)
        footer.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)

        ttk.Label(
            footer,
            textvariable=self.status_var,
            style="Status.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            footer,
            text=(
                "Bind: o painel abre o F8 automaticamente. "
                "Comer/Beber: mantenha o FiveM como janela ativa."
            ),
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _get_command_text(self) -> str:
        return self.command_text.get("1.0", "end-1c").strip()

    def _refresh_preview(self) -> None:
        key = self.key_var.get().strip().upper() or "<TECLA>"

        if hasattr(self, "command_text"):
            command = self._get_command_text()
        else:
            command = "<COMANDO>"

        self.preview_unbind_var.set(f'unbind "{key}"')
        self.preview_bind_var.set(f'bind keyboard "{key}" "{command}"')

    def _refresh_tree(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for index, item in enumerate(self.items):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(item.name, item.key, item.command),
            )

    def _read_form(self) -> BindItem:
        key = FiveMBindService.validate_key(self.key_var.get())
        command = FiveMBindService.validate_command(self._get_command_text())
        name = self.name_var.get().strip() or f"Bind {key}"

        return BindItem(name=name, key=key, command=command)

    def save_current(self) -> None:
        try:
            item = self._read_form()
        except ValueError as exc:
            messagebox.showwarning("Dados invalidos", str(exc), parent=self)
            return

        existing_index = next(
            (
                index
                for index, saved in enumerate(self.items)
                if saved.key == item.key
            ),
            None,
        )

        if existing_index is None:
            self.items.append(item)
            self.status_var.set(f"Bind {item.key} salva na lista.")
        else:
            self.items[existing_index] = item
            self.status_var.set(f"Bind {item.key} atualizada na lista.")

        try:
            self.repository.save(self.items)
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=self)
            return

        self._refresh_tree()

    def load_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.tree.selection()

        if not selection:
            return

        index = int(selection[0])
        item = self.items[index]

        self.name_var.set(item.name)
        self.key_var.set(item.key)

        self.command_text.delete("1.0", "end")
        self.command_text.insert("1.0", item.command)

        self._refresh_preview()
        self.status_var.set(f"Bind {item.key} carregada para edicao.")

    def delete_selected(self) -> None:
        selection = self.tree.selection()

        if not selection:
            messagebox.showinfo("Excluir", "Selecione uma bind salva.", parent=self)
            return

        index = int(selection[0])
        item = self.items[index]

        confirm = messagebox.askyesno(
            "Excluir bind salva",
            (
                f"Excluir '{item.name}' ({item.key}) da lista local?\n\n"
                "Isso nao remove a bind do FiveM. "
                "Use 'Somente limpar' para isso."
            ),
            parent=self,
        )

        if not confirm:
            return

        del self.items[index]

        try:
            self.repository.save(self.items)
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc), parent=self)
            return

        self._refresh_tree()
        self.status_var.set(f"Bind {item.key} removida da lista local.")

    def new_form(self) -> None:
        self.name_var.set("")
        self.key_var.set("6")

        self.command_text.delete("1.0", "end")
        self.command_text.insert("1.0", "e meditar4;e continencia2")

        self._refresh_preview()
        self.status_var.set("Novo cadastro iniciado.")

    def _get_delay(self) -> float:
        try:
            delay = float(self.delay_var.get())
        except (tk.TclError, ValueError) as exc:
            raise ValueError("Informe um atraso valido em segundos.") from exc

        if not 0.5 <= delay <= 10.0:
            raise ValueError("O atraso deve ficar entre 0,5 e 10 segundos.")

        return delay

    def _set_execution_state(self, executing: bool) -> None:
        self.is_executing = executing
        state = "disabled" if executing else "normal"

        self.apply_button.configure(state=state)
        self.unbind_button.configure(state=state)

    def apply_bind(self) -> None:
        if self.is_executing:
            return

        try:
            item = self._read_form()
            delay = self._get_delay()
        except ValueError as exc:
            messagebox.showwarning("Dados invalidos", str(exc), parent=self)
            return

        self._set_execution_state(True)
        self.status_var.set(
            f"Aplicando {item.key} em {delay:.1f}s. O painel sera minimizado..."
        )
        self.iconify()

        thread = threading.Thread(
            target=self._apply_worker,
            args=(item, delay),
            daemon=True,
        )
        thread.start()

    def _apply_worker(self, item: BindItem, delay: float) -> None:
        try:
            FiveMBindService.execute_apply(item.key, item.command, delay)
        except Exception as exc:
            self.after(0, lambda: self._execution_error(exc))
            return

        self.after(0, lambda: self._execution_success(item.key, "aplicada"))

    def clear_bind(self) -> None:
        if self.is_executing:
            return

        try:
            key = FiveMBindService.validate_key(self.key_var.get())
            delay = self._get_delay()
        except ValueError as exc:
            messagebox.showwarning("Dados invalidos", str(exc), parent=self)
            return

        self._set_execution_state(True)
        self.status_var.set(
            f"Limpando {key} em {delay:.1f}s. O painel sera minimizado..."
        )
        self.iconify()

        thread = threading.Thread(
            target=self._unbind_worker,
            args=(key, delay),
            daemon=True,
        )
        thread.start()

    def _unbind_worker(self, key: str, delay: float) -> None:
        try:
            FiveMBindService.execute_unbind(key, delay)
        except Exception as exc:
            self.after(0, lambda: self._execution_error(exc))
            return

        self.after(0, lambda: self._execution_success(key, "removida"))

    def _execution_success(self, key: str, action: str) -> None:
        self._set_execution_state(False)
        self.deiconify()
        self.lift()
        self.status_var.set(f"Bind {key} {action} com sucesso.")

    def _execution_error(self, exc: Exception) -> None:
        self._set_execution_state(False)
        self.deiconify()
        self.lift()
        self.status_var.set("Falha durante a automacao.")

        messagebox.showerror(
            "Erro na automacao",
            f"Nao foi possivel concluir a operacao:\n\n{exc}",
            parent=self,
        )

    def _read_automation_config(self) -> AutomationConfig:
        try:
            eat_minutes = float(self.eat_minutes_var.get())
            drink_minutes = float(self.drink_minutes_var.get())
        except (tk.TclError, ValueError) as exc:
            raise ValueError("Informe os intervalos em minutos corretamente.") from exc

        config = AutomationConfig(
            eat_enabled=bool(self.eat_enabled_var.get()),
            eat_key=self.eat_key_var.get().strip().upper(),
            eat_minutes=eat_minutes,
            drink_enabled=bool(self.drink_enabled_var.get()),
            drink_key=self.drink_key_var.get().strip().upper(),
            drink_minutes=drink_minutes,
        )

        return PeriodicKeyAutomation.validate_config(config)

    def start_periodic_automation(self) -> None:
        try:
            config = self._read_automation_config()
        except ValueError as exc:
            messagebox.showwarning("Automacao", str(exc), parent=self)
            return

        try:
            self.automation_repository.save(config)
        except OSError as exc:
            messagebox.showerror(
                "Erro ao salvar configuracao",
                str(exc),
                parent=self,
            )
            return

        self.periodic_automation.start(config)
        self.automation_config = config
        self._refresh_automation_controls()
        self.automation_status_var.set(
            "Automacao ativa. Deixe o FiveM em primeiro plano."
        )
        self.status_var.set("Automacao Comer / Beber iniciada.")

        # Minimiza o painel para facilitar o retorno ao FiveM.
        self.iconify()

    def stop_periodic_automation(self) -> None:
        self.periodic_automation.stop()
        self._refresh_automation_controls()
        self.eat_countdown_var.set("--:--")
        self.drink_countdown_var.set("--:--")
        self.automation_status_var.set("Automacao parada.")
        self.status_var.set("Automacao Comer / Beber parada.")

    def _refresh_automation_controls(self) -> None:
        active = bool(self.periodic_automation.snapshot()["active"])

        self.start_automation_button.configure(
            state="disabled" if active else "normal"
        )
        self.stop_automation_button.configure(
            state="normal" if active else "disabled"
        )

        eat_state = "normal" if self.eat_enabled_var.get() and not active else "disabled"
        drink_state = (
            "normal" if self.drink_enabled_var.get() and not active else "disabled"
        )

        self.eat_key_combo.configure(state=eat_state)
        self.eat_minutes_spin.configure(state=eat_state)
        self.drink_key_combo.configure(state=drink_state)
        self.drink_minutes_spin.configure(state=drink_state)

    @staticmethod
    def _format_countdown(seconds: float | None) -> str:
        if seconds is None:
            return "--:--"

        total_seconds = max(0, int(math.ceil(seconds)))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"

        return f"{minutes:02d}:{secs:02d}"

    def _update_automation_ui(self) -> None:
        snapshot = self.periodic_automation.snapshot()
        active = bool(snapshot["active"])

        if active:
            self.eat_countdown_var.set(
                self._format_countdown(snapshot["eat_remaining"])  # type: ignore[arg-type]
            )
            self.drink_countdown_var.set(
                self._format_countdown(snapshot["drink_remaining"])  # type: ignore[arg-type]
            )

            last_action = str(snapshot["last_action"])
            last_action_at = str(snapshot["last_action_at"])

            if last_action:
                self.automation_status_var.set(
                    f"Ativa | Ultima: {last_action} as {last_action_at}"
                )
            else:
                self.automation_status_var.set(
                    "Automacao ativa. Aguardando o primeiro intervalo."
                )
        else:
            self.eat_countdown_var.set("--:--")
            self.drink_countdown_var.set("--:--")

        self.after(250, self._update_automation_ui)

    def _on_close(self) -> None:
        self.periodic_automation.stop()
        self.destroy()


def main() -> None:
    app = BindPanel()
    app.mainloop()


if __name__ == "__main__":
    main()