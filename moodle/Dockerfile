FROM php:8.1-apache

# Install PHP extensions and tools
RUN apt-get update && apt-get install -y \
    libpng-dev libjpeg-dev libfreetype6-dev \
    zip unzip libzip-dev libicu-dev libxml2-dev \
    libcurl4-openssl-dev libonig-dev libxslt1-dev \
    netcat-traditional \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install gd mysqli pdo pdo_mysql intl zip soap mbstring exif opcache xsl \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# Download Moodle 4.4.0 from GitHub
WORKDIR /var/www/html
RUN curl -L https://github.com/moodle/moodle/archive/refs/tags/v4.4.0.tar.gz -o /tmp/moodle.tar.gz \
    && tar -xzf /tmp/moodle.tar.gz -C /var/www/html --strip-components=1 \
    && rm /tmp/moodle.tar.gz \
    && chown -R www-data:www-data /var/www/html

# Moodledata directory
RUN mkdir -p /var/www/moodledata && chown -R www-data:www-data /var/www/moodledata

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["apache2-foreground"]
