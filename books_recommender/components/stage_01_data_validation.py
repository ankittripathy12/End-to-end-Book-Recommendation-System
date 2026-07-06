import os
import sys
import ast
import pickle
import pandas as pd

from books_recommender.logger.log import logging
from books_recommender.config.configuration import AppConfiguration
from books_recommender.exception.exception_handler import AppException


class DataValidation:
    def __init__(self, app_config=AppConfiguration()):
        try:
            self.data_validation_config = app_config.get_data_validation_config()
        except Exception as e:
            raise AppException(e, sys) from e

    def preprocess_data(self):
        try:
            # Load datasets
            ratings = pd.read_csv(
                self.data_validation_config.ratings_csv_file,
                sep=";",
                encoding="latin-1",
                on_bad_lines="skip"
            )

            books = pd.read_csv(
                self.data_validation_config.books_csv_file,
                sep=";",
                encoding="latin-1",
                on_bad_lines="skip"
            )

            logging.info(f"Shape of ratings data file: {ratings.shape}")
            logging.info(f"Shape of books data file: {books.shape}")

            # Keep only required columns
            books = books[
                [
                    "ISBN",
                    "Book-Title",
                    "Book-Author",
                    "Year-Of-Publication",
                    "Publisher",
                    "Image-URL-L",
                ]
            ]

            # Rename columns
            books.rename(
                columns={
                    "Book-Title": "title",
                    "Book-Author": "author",
                    "Year-Of-Publication": "year",
                    "Publisher": "publisher",
                    "Image-URL-L": "image_url",
                },
                inplace=True,
            )

            ratings.rename(
                columns={
                    "User-ID": "user_id",
                    "Book-Rating": "rating",
                },
                inplace=True,
            )

            # Users who rated more than 200 books
            active_users = ratings["user_id"].value_counts()
            active_users = active_users[active_users > 200].index

            ratings = ratings[ratings["user_id"].isin(active_users)]

            # Merge ratings with books
            ratings_with_books = ratings.merge(books, on="ISBN")

            # Count ratings per book
            number_rating = (
                ratings_with_books.groupby("title")["rating"]
                .count()
                .reset_index()
            )

            number_rating.rename(
                columns={"rating": "num_of_rating"},
                inplace=True,
            )

            final_rating = ratings_with_books.merge(
                number_rating,
                on="title",
            )

            # Books having at least 50 ratings
            final_rating = final_rating[
                final_rating["num_of_rating"] >= 50
            ]

            # Remove duplicate user-book ratings
            final_rating.drop_duplicates(
                ["user_id", "title"],
                inplace=True,
            )

            logging.info(
                f"Shape of the final clean dataset: {final_rating.shape}"
            )

            # Save cleaned CSV
            os.makedirs(
                self.data_validation_config.clean_data_dir,
                exist_ok=True,
            )

            clean_csv_path = os.path.join(
                self.data_validation_config.clean_data_dir,
                "clean_data.csv",
            )

            final_rating.to_csv(
                clean_csv_path,
                index=False,
            )

            logging.info(f"Saved cleaned data to {clean_csv_path}")

            # Save pickle
            os.makedirs(
                self.data_validation_config.serialized_objects_dir,
                exist_ok=True,
            )

            pickle_path = os.path.join(
                self.data_validation_config.serialized_objects_dir,
                "final_rating.pkl",
            )

            with open(pickle_path, "wb") as file:
                pickle.dump(final_rating, file)

            logging.info(
                f"Saved final_rating serialization object to {pickle_path}"
            )

        except Exception as e:
            raise AppException(e, sys) from e

    def initiate_data_validation(self):
        try:
            logging.info("=" * 20 + " Data Validation Started " + "=" * 20)
            self.preprocess_data()
            logging.info("=" * 20 + " Data Validation Completed " + "=" * 20)
        except Exception as e:
            raise AppException(e, sys) from e