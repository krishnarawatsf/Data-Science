import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error


def train_simple_revenue_model(df: pd.DataFrame, features, target='Revenue'):
    df = df.copy()
    df = df.dropna(subset=[target])
    X = df[features].select_dtypes(include=['number']).fillna(0)
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return model, {'r2': r2_score(y_test, preds), 'mae': mean_absolute_error(y_test, preds)}
