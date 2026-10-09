"""Predicción del precio de casas en California.

Plantilla completada a partir de los TODO.
Autores: Daniel Bernal Anzano
"""
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.datasets import fetch_california_housing
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, plot_tree

TARGET = "MedHouseVal"
RANDOM_STATE = 42
TEST_SIZE = 0.2
MAX_DEPTH = 5
DEFAULT_PLOT_DEPTH = 2
MAX_PLOT_DEPTH_LIMIT = 4
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = str(BASE_DIR / "modelo_california.pkl")


def check_nulls(df: pd.DataFrame):
    """Muestra por pantalla el número de valores nulos por columna."""
    null_counts = df.isna().sum()
    print("Daniel Bernal Anzano | P1")
    print("Valores nulos por columna:")
    print(null_counts.to_string())
    return null_counts


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Descarta las filas con valores nulos y devuelve el DataFrame."""
    rows_before = len(df)
    clean_df = df.dropna().reset_index(drop=True)
    print(f"Filas antes: {rows_before}")
    print(f"Filas después: {len(clean_df)}")
    print(f"Filas descartadas: {rows_before - len(clean_df)}")
    return clean_df


def validate_max_depth(max_depth=None) -> int:
    """Valida `max_depth` y devuelve la profundidad finalmente usada.

    Si no se indica, no es un entero válido o supera un límite razonable,
    se recurre al valor por defecto `DEFAULT_PLOT_DEPTH`.
    """
    if isinstance(max_depth, bool) or not isinstance(max_depth, int):
        print(f"max_depth no indicado o inválido ({max_depth!r}): "
              f"se usa el valor por defecto ({DEFAULT_PLOT_DEPTH}).")
        return DEFAULT_PLOT_DEPTH
    if max_depth < 1:
        print(f"max_depth={max_depth} no es válido (mínimo 1): "
              f"se usa el valor por defecto ({DEFAULT_PLOT_DEPTH}).")
        return DEFAULT_PLOT_DEPTH
    if max_depth > MAX_PLOT_DEPTH_LIMIT:
        print(f"max_depth={max_depth} supera el límite razonable "
              f"({MAX_PLOT_DEPTH_LIMIT}): se usa {MAX_PLOT_DEPTH_LIMIT}.")
        return MAX_PLOT_DEPTH_LIMIT
    return max_depth


def plot_decision_tree(X, y, max_depth=None):
    """Dibuja un árbol de decisión y guarda la imagen.

    Valida `max_depth` antes de entrenar el árbol, de modo que la imagen
    mostrada llega siempre hasta hojas reales.
    """
    depth = validate_max_depth(max_depth)
    tree = DecisionTreeRegressor(max_depth=depth, random_state=RANDOM_STATE)
    tree.fit(X, y)

    image_path = str(BASE_DIR / "arbol_decision.png")
    feature_names = list(X.columns) if hasattr(X, "columns") else None

    n_leaves = tree.get_n_leaves()
    fig_w = min(max(3.0 * n_leaves, 8.0), 16.0)
    fig_h = 2.2 * (tree.get_depth() + 1)
    print(f"Hojas: {n_leaves} | nodos: {tree.tree_.node_count} | lienzo: {fig_w:.0f}x{fig_h:.0f} in")

    plt.figure(figsize=(fig_w, fig_h))
    plot_tree(
        tree,
        feature_names=feature_names,
        filled=True,
        fontsize=12,
    )
    plt.title(f"Árbol de decisión (max_depth={depth}) - Daniel Bernal Anzano | P1")
    plt.tight_layout()
    plt.savefig(image_path, dpi=400, bbox_inches="tight")
    plt.close()
    print(f"Profundidad real del árbol dibujado: {tree.get_depth()}")
    print(f"Árbol guardado en: {image_path}")
    return image_path


def compute_errors(y_true, y_pred, print_errors: bool = True) -> tuple[float, float]:
    """Calcula el MAE y el MSE entre los valores reales y las predicciones.

    Si `print_errors` es True (por defecto), los muestra por pantalla.
    """
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    if print_errors:
        print(f"MAE: {mae:.4f}")
        print(f"MSE: {mse:.4f}")
    return mae, mse


def save_model(model, path: str = MODEL_PATH):
    """Guarda el modelo entrenado en `path` usando joblib.dump()."""
    joblib.dump(model, path)
    print(f"Modelo guardado en: {path}")
    return path


def validate_data():
    """Exploración y validación de los datos."""
    df = fetch_california_housing(as_frame=True).frame
    check_nulls(df)
    df = handle_nulls(df)


def build_model():
    """Carga los datos, entrena el modelo, muestra sus errores y lo devuelve."""
    df = fetch_california_housing(as_frame=True).frame

    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    model = DecisionTreeRegressor(max_depth=MAX_DEPTH, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    compute_errors(y_test, y_pred)

    return model


def plot_data():
    """Visualización: dibuja un árbol de decisión pequeño del dataset."""
    df = fetch_california_housing(as_frame=True).frame
    X = df.dropna().drop(columns=[TARGET])
    y = df.dropna()[TARGET]
    plot_decision_tree(X, y, max_depth=None)


def main():
    model = build_model()
    save_model(model)


if __name__ == "__main__":
    validate_data()
    plot_data()
    main()
